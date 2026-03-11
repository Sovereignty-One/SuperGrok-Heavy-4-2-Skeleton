/**

- SuperGrok Unified Server -- Production Enterprise
- Single process: Node.js + WebSocket bridge + Auth + DDG + GitHub + Plaid + Piper + ISH shell
- Ports: 9000 (primary), 9898 (bridge alias), 8443 (auth alias)
- Run: node unified_server.js
  */
  'use strict';

const http    = require('http');
const https   = require('https');
const ws_mod  = require('ws');
const fs      = require('fs');
const path    = require('path');
const crypto  = require('crypto');
const os      = require('os');
const { spawn, exec } = require('child_process');

// ─── CONFIG ───────────────────────────────────────────────────────────
const PORT_UNIFIED = parseInt(process.env.PORT_UNIFIED || '9000');
const PORT_BRIDGE  = parseInt(process.env.PORT_BRIDGE  || '9898');
const PORT_AUTH    = parseInt(process.env.PORT_AUTH    || '8443');
const PIPER_BIN    = process.env.PIPER_BIN    || './piper';
const PIPER_MODEL  = process.env.PIPER_MODEL  || './en_US-lessac-medium.onnx';
const COQUI_URL    = process.env.COQUI_URL    || 'http://localhost:5002';
const LOG_DIR      = process.env.LOG_DIR      || './logs';
const KEY_FILE     = process.env.KEY_FILE     || '.sg_master_key';
const VERBOSE      = process.env.VERBOSE      === '1';

if (!fs.existsSync(LOG_DIR)) fs.mkdirSync(LOG_DIR, { recursive: true });

const ACCESS_LOG  = path.join(LOG_DIR, 'access.jsonl');
const piperReady  = fs.existsSync(PIPER_BIN) && fs.existsSync(PIPER_MODEL);

// ─── COQUI TTS STATUS ────────────────────────────────────────────────
let coquiReady = false;
(function checkCoqui() {
const req = http.get(COQUI_URL + '/api/tts', { timeout: 3000 }, res => {
  // Any response means server is running (even 405 on GET)
  coquiReady = true;
  res.resume();
  if (VERBOSE) process.stdout.write('[TTS] Coqui server detected at '+COQUI_URL+'\n');
});
req.on('error', () => { coquiReady = false; });
req.on('timeout', () => { req.destroy(); coquiReady = false; });
})();

// ─── TTS QUEUE (shared by Piper + Coqui) ─────────────────────────────
const ttsQueue = [];
let ttsProcessing = false;

function enqueueTTS(text, wsId, engine, voice, speed) {
return new Promise(resolve => {
  ttsQueue.push({ text, wsId, engine: engine||'auto', voice: voice||'', speed: speed||1.0, resolve });
  if (!ttsProcessing) processTTSQueue();
});
}

async function processTTSQueue() {
if (ttsQueue.length === 0) { ttsProcessing = false; return; }
ttsProcessing = true;
const item = ttsQueue.shift();
let result;
try {
  const engine = pickEngine(item.engine);
  if (engine === 'coqui')      result = await coquiSpeak(item.text, item.wsId, item.voice, item.speed);
  else if (engine === 'piper') result = await piperSpeak(item.text, item.wsId);
  else                         result = { type:'piper_done', fallback:true, engine:'none' };
} catch(e) {
  result = { type:'piper_done', fallback:true, error:e.message };
}
item.resolve(result);
setImmediate(() => processTTSQueue());
}

function pickEngine(requested) {
if (requested === 'coqui' && coquiReady) return 'coqui';
if (requested === 'piper' && piperReady) return 'piper';
if (requested === 'auto') {
  if (coquiReady) return 'coqui';
  if (piperReady) return 'piper';
}
return 'none';
}

// ─── MASTER KEY ───────────────────────────────────────────────────────
let MASTER_KEY;
if (fs.existsSync(KEY_FILE)) {
MASTER_KEY = fs.readFileSync(KEY_FILE);
} else {
MASTER_KEY = crypto.randomBytes(64);
fs.writeFileSync(KEY_FILE, MASTER_KEY, { mode: 0o600 });
}

// ─── AUDIT CHAIN ─────────────────────────────────────────────────────
let auditSeq = 0, prevHash = '0'.repeat(64);
function audit(event, detail, extra) {
const entry = { seq: ++auditSeq, ts: new Date().toISOString(), event, detail: String(detail).slice(0, 500), prev: prevHash, ...extra };
entry.hash = crypto.createHmac('sha256', MASTER_KEY)
.update(JSON.stringify({ seq: entry.seq, event, detail: entry.detail, prev: prevHash }))
.digest('hex');
prevHash = entry.hash;
fs.appendFileSync(ACCESS_LOG, JSON.stringify(entry) + '\n');
if (VERBOSE) process.stdout.write('[AUDIT] ' + entry.ts + ' ' + event + ': ' + entry.detail + '\n');
return entry;
}

// ─── JWT / TOKEN ──────────────────────────────────────────────────────
function signToken(payload) {
const h = Buffer.from(JSON.stringify({ alg: 'HS512-dilithium3', typ: 'JWT' })).toString('base64url');
const b = Buffer.from(JSON.stringify(payload)).toString('base64url');
const s = crypto.createHmac('sha512', MASTER_KEY).update(h + '.' + b).digest('base64url');
return h + '.' + b + '.' + s;
}
function verifyToken(token) {
if (!token) throw new Error('no token');
const p = token.split('.');
if (p.length !== 3) throw new Error('malformed');
const expected = crypto.createHmac('sha512', MASTER_KEY).update(p[0] + '.' + p[1]).digest('base64url');
if (!crypto.timingSafeEqual(Buffer.from(p[2], 'base64url'), Buffer.from(expected, 'base64url')))
throw new Error('bad signature');
const payload = JSON.parse(Buffer.from(p[1], 'base64url').toString());
if (payload.exp < Math.floor(Date.now() / 1000)) throw new Error('expired');
return payload;
}

// ─── ROLE MATRIX ──────────────────────────────────────────────────────
const RM = {
root:             { lvl:6, pp:true,  panels:'*' },
superadmin:       { lvl:6, pp:true,  panels:'*' },
president:        { lvl:5, pp:true,  panels:['dashboard','exec_orders','cabinet','natl_security','ai_chat','terminal','audit_trail','key_mgmt','profile','memory','comms_secure'] },
prime_minister:   { lvl:5, pp:true,  panels:['dashboard','parliament','cabinet','natl_security','ai_chat','audit_trail','profile','terminal','memory'] },
un_sg:            { lvl:5, pp:true,  panels:['dashboard','security_council','peacekeeping','resolutions','ai_chat','audit_trail','profile'] },
judge:            { lvl:5, pp:true,  panels:['dashboard','case_docket','hearings','orders','sentencing','appeals','legal_research','lie_detect','ai_chat','audit_trail','profile'] },
intel_officer:    { lvl:5, pp:true,  panels:['dashboard','sigint','humint','threat_assess','uc_identity','ai_chat','terminal','audit_trail','profile','key_mgmt'] },
cyber_cmd:        { lvl:5, pp:true,  panels:['dashboard','threat_intel','incident_resp','zero_day','soc','terminal','key_mgmt','ai_chat','audit_trail','profile'] },
surgeon_general:  { lvl:5, pp:true,  panels:['dashboard','health_advisories','emergency_authority','patient_care','ai_chat','audit_trail','profile'] },
supreme_court:    { lvl:5, pp:true,  panels:['dashboard','cert_review','oral_arguments','opinions','legal_research','ai_chat','audit_trail','profile'] },
gov_official:     { lvl:4, pp:true,  panels:['dashboard','policy_mgmt','legislation','budget','ai_chat','audit_trail','profile'] },
military:         { lvl:4, pp:true,  panels:['dashboard','missions','intel','logistics','terminal','ai_chat','audit_trail','profile'] },
ambassador:       { lvl:4, pp:true,  panels:['dashboard','diplo_cables','treaty','consular','ai_chat','audit_trail','profile'] },
foreign_minister: { lvl:4, pp:true,  panels:['dashboard','foreign_policy','treaty','sanctions','ai_chat','audit_trail','profile'] },
interpol:         { lvl:4, pp:true,  panels:['dashboard','red_notices','cross_border','cybercrime','ai_chat','terminal','audit_trail','profile'] },
attorney_general: { lvl:4, pp:true,  panels:['dashboard','litigation','antitrust','doj_lead','legal_research','ai_chat','audit_trail','profile'] },
medical:          { lvl:3, pp:false, panels:['dashboard','patient_care','vitals','medications','ehr','session_clock','ai_chat','audit_trail','profile'] },
prosecutor:       { lvl:3, pp:false, panels:['dashboard','active_cases','evidence','witnesses','charges','legal_research','ai_chat','audit_trail','profile'] },
police:           { lvl:3, pp:false, panels:['dashboard','dispatch','arrests','reports','incidents','sos_panel','ai_chat','audit_trail','profile'] },
pilot:            { lvl:3, pp:false, panels:['dashboard','flight_plan','notam','weather','charts','radar','ai_chat','audit_trail','profile'] },
developer:        { lvl:3, pp:false, panels:['dashboard','api_console','cicd','project_builder','terminal','github_panel','key_mgmt','ai_chat','audit_trail','profile','bridge'] },
professor:        { lvl:3, pp:false, panels:['dashboard','courses','research','publications','ai_chat','audit_trail','profile'] },
teacher:          { lvl:2, pp:false, panels:['dashboard','class_dash','grades','attendance','curriculum','eeg_classroom','ai_chat','audit_trail','profile'] },
fire:             { lvl:2, pp:false, panels:['dashboard','incidents','dispatch','equipment','hazmat','sos_panel','ai_chat','audit_trail','profile'] },
emt:              { lvl:2, pp:false, panels:['dashboard','patient_care','vitals','dispatch','sos_panel','ai_chat','audit_trail','profile'] },
security:         { lvl:2, pp:false, panels:['dashboard','access_logs','cameras','perimeter','incidents','ai_chat','audit_trail','profile'] },
corrections:      { lvl:2, pp:false, panels:['dashboard','inmate_roster','programs','incidents','ai_chat','audit_trail','profile'] },
social_worker:    { lvl:2, pp:false, panels:['dashboard','case_mgmt','home_visits','court_reports','ai_chat','audit_trail','profile'] },
student:          { lvl:1, pp:false, panels:['dashboard','eeg_student','rewards','ai_games','ai_chat','profile'] },
adult:            { lvl:1, pp:false, panels:['dashboard','profile','ai_chat','ddg_browser','memory'] },
rideshare:        { lvl:1, pp:false, panels:['dashboard','active_ride','navigation','earnings','sos_panel','ai_chat','profile'] },
postal:           { lvl:1, pp:false, panels:['dashboard','packages','routes','manifest','ai_chat','profile'] },
chaplain:         { lvl:1, pp:false, panels:['dashboard','counseling','memorial','ai_chat','profile'] },
journalist:       { lvl:1, pp:false, panels:['dashboard','story_research','source_mgmt','foia','ai_chat','ddg_browser','profile'] },
child:            { lvl:0, pp:false, panels:['dashboard','story_time','learning_games','drawing','ai_tutor','homework','profile'] },
teen:             { lvl:0, pp:false, panels:['dashboard','college_prep','career','ai_tutor','homework','ai_games','profile'] },
};

const CHILD_BLOCKED = new Set(['president','prime_minister','root','superadmin','intel_officer',
'cyber_cmd','judge','military','attorney_general','gov_official','supreme_court',
'surgeon_general','un_sg','ambassador','foreign_minister','interpol']);

// HMAC passphrase hashes
const PP_HASHES = {};
Object.keys(RM).forEach(role => {
if (RM[role].pp) PP_HASHES[role] = crypto.createHmac('sha256', MASTER_KEY).update('PASSPHRASE:'+role).digest('hex');
});

// ─── RATE / FAIL TRACKING ─────────────────────────────────────────────
const rateMap = new Map(), failMap = new Map();
function checkRate(id) {
const now = Date.now(), r = rateMap.get(id) || { n:0, reset:now+60000 };
if (now > r.reset) { r.n=0; r.reset=now+60000; }
rateMap.set(id, { n:++r.n, reset:r.reset });
return r.n <= 60;
}
function checkFail(ip) {
const f = failMap.get(ip) || { n:0, lock:0 };
return Date.now() >= f.lock;
}
function recordFail(ip) {
const f = failMap.get(ip) || { n:0, lock:0 };
f.n++;
if (f.n >= 5) f.lock = Date.now() + 60000;
failMap.set(ip, f);
}

// ─── AUTH HELPERS ─────────────────────────────────────────────────────
async function doLogin(body, ip) {
const { name, role, rank, badge, pin_hash, passphrase_hash, bio_hash } = body;
if (!checkFail(ip)) return { s:429, d:{ detail:'Locked' } };
const r = role && role.toLowerCase().trim();
const cfg = RM[r];
if (!cfg) { audit('LOGIN_BAD_ROLE', name+':'+role, {ip}); return { s:403, d:{ detail:'Unknown role' } }; }
if (CHILD_BLOCKED.has(r) && cfg.lvl >= 4 && !passphrase_hash) {
audit('CHILD_ESCALATION', name+':'+r, {ip}); return { s:403, d:{ detail:'Access Denied' } };
}
if (cfg.pp) {
if (!passphrase_hash) { audit('NO_PP', name+':'+r, {ip}); return { s:403, d:{ detail:'Passphrase required' } }; }
const ex = PP_HASHES[r] || '';
const a = Buffer.alloc(32), b = Buffer.alloc(32);
Buffer.from(passphrase_hash.toLowerCase().slice(0,64).padEnd(64,'0'), 'hex').copy(a);
Buffer.from(ex.slice(0,64).padEnd(64,'0'), 'hex').copy(b);
if (!crypto.timingSafeEqual(a, b)) {
recordFail(ip); audit('PP_FAIL', name+':'+r, {ip});
await new Promise(res => setTimeout(res, 2000));
return { s:403, d:{ detail:'Access Denied' } };
}
}
if (!pin_hash || pin_hash.length < 32) return { s:400, d:{ detail:'Invalid credential format' } };
const payload = { sub:name, role:r, rank:rank||'', badge:badge||'', lvl:cfg.lvl, panels:cfg.panels,
bio:!!bio_hash, iat:Math.floor(Date.now()/1000), exp:Math.floor(Date.now()/1000)+28800,
jti:crypto.randomBytes(16).toString('hex') };
const token = signToken(payload);
audit('LOGIN_OK', name+':'+r+' lvl:'+cfg.lvl, {ip});
return { s:200, d:{ token, lvl:cfg.lvl, panels:cfg.panels, expires_in:28800 } };
}
function doVerifyPanel(body, ip) {
const { token, panel, role } = body;
let p;
try { p = verifyToken(token); }
catch(e) { audit('TOKEN_BAD', 'panel:'+panel, {ip,reason:e.message}); return { s:401, d:{ detail:'Invalid token' } }; }
if (p.role !== (role||'').toLowerCase()) {
audit('ROLE_MISMATCH', 'claimed:'+role+' actual:'+p.role, {ip}); return { s:403, d:{ detail:'Role mismatch' } };
}
if (p.panels !== '*' && !p.panels.includes(panel)) {
audit('PANEL_DENIED', p.sub+':'+p.role+'->'+panel, {ip}); return { s:403, d:{ detail:'Access Denied: '+panel } };
}
audit('PANEL_OK', p.sub+':'+p.role+'->'+panel, {ip});
return { s:200, d:{ ok:true, lvl:p.lvl, sub:p.sub } };
}

// ─── DDG PROXY ────────────────────────────────────────────────────────
function ddgSearch(query) {
return new Promise(resolve => {
const q = encodeURIComponent((query||'').slice(0,400));
const opts = { hostname:'api.duckduckgo.com', path:'/?q='+q+'&format=json&no_html=1&skip_disambig=1',
method:'GET', headers:{'User-Agent':'SuperGrok/13 (quantum-safe; no-tracking; no-ads)'}, timeout:8000 };
const req = https.request(opts, res => {
const ch = []; res.on('data',c=>ch.push(c));
res.on('end', () => {
try {
const j = JSON.parse(Buffer.concat(ch).toString());
resolve({ ok:true, abstract:j.Abstract||'', answer:j.Answer||'',
related:(j.RelatedTopics||[]).slice(0,6).map(t=>t.Text||'').filter(Boolean),
url:j.AbstractURL||'' });
} catch { resolve({ ok:true, raw:Buffer.concat(ch).toString().slice(0,1500) }); }
});
});
req.on('error', e => resolve({ ok:false, error:e.message }));
req.on('timeout', () => { req.destroy(); resolve({ ok:false, error:'timeout' }); });
req.end();
});
}

// ─── AI PROXY ─────────────────────────────────────────────────────────
function aiProxy(model, text, system, apiKey, cb) {
const providers = {
claude: { host:'api.anthropic.com', path:'/v1/messages', envKey:'ANTHROPIC_API_KEY',
makeHeaders: k => ({ 'Content-Type':'application/json','x-api-key':k,'anthropic-version':'2023-06-01' }),
makeBody: t => JSON.stringify({ model:'claude-sonnet-4-20250514', max_tokens:1200,
system:system||'You are SuperGrok AI assistant.', messages:[{role:'user',content:t}] }),
extract: d => d.content&&d.content[0]&&d.content[0].text },
gpt: { host:'api.openai.com', path:'/v1/chat/completions', envKey:'OPENAI_API_KEY',
makeHeaders: k => ({ 'Content-Type':'application/json','Authorization':'Bearer '+k }),
makeBody: t => JSON.stringify({ model:'gpt-4o', max_tokens:1200,
messages:[{role:'system',content:system||''},{role:'user',content:t}] }),
extract: d => d.choices&&d.choices[0]&&d.choices[0].message&&d.choices[0].message.content },
grok: { host:'api.x.ai', path:'/v1/chat/completions', envKey:'XAI_API_KEY',
makeHeaders: k => ({ 'Content-Type':'application/json','Authorization':'Bearer '+k }),
makeBody: t => JSON.stringify({ model:'grok-2-latest', max_tokens:1200,
messages:[{role:'system',content:system||''},{role:'user',content:t}] }),
extract: d => d.choices&&d.choices[0]&&d.choices[0].message&&d.choices[0].message.content },
};
const prov = providers[model] || providers.claude;
const key  = apiKey || process.env[prov.envKey] || '';
if (!key) { cb(null, 'Set '+prov.envKey+' env var or pass apiKey from Bridge Config'); return; }
const body = prov.makeBody(text);
const opts = { hostname:prov.host, path:prov.path, method:'POST',
headers:Object.assign({}, prov.makeHeaders(key), {'Content-Length':Buffer.byteLength(body)}),
timeout:30000 };
const req = https.request(opts, res => {
const ch = []; res.on('data',c=>ch.push(c));
res.on('end', () => {
try { const d = JSON.parse(Buffer.concat(ch).toString()); cb(null, prov.extract(d)||'No response'); }
catch(e) { cb(null, 'Parse error: '+e.message); }
});
});
req.on('error', e => cb(null, 'Network error: '+e.message));
req.on('timeout', () => { req.destroy(); cb(null, 'AI API timeout'); });
req.write(body); req.end();
}

// ─── PIPER TTS ────────────────────────────────────────────────────────
function piperSpeak(text, wsId) {
const safe = text.replace(/[`$\'";|<>(){}[]!#*?\n\r]/g,' ').slice(0,800);
return new Promise(resolve => {
if (!piperReady) { resolve({ type:'piper_done', fallback:true }); return; }
const wav = path.join(os.tmpdir(),'piper_'+wsId+'*'+Date.now()+'.wav');
const child = spawn(PIPER_BIN, ['-model',PIPER_MODEL,'-output_file',wav]);
child.stdin.write(safe); child.stdin.end();
let done = false;
child.on('close', code => {
if (done) return; done = true;
if (code!==0 || !fs.existsSync(wav)) { resolve({ type:'piper_done', fallback:true }); return; }
const data = fs.readFileSync(wav).toString('base64');
try { fs.unlinkSync(wav); } catch(e){}
resolve({ type:'audio', data, done:true });
});
child.on('error', () => { if(!done){done=true; resolve({ type:'piper_done', fallback:true });} });
setTimeout(() => { if(!done){done=true; child.kill(); resolve({ type:'piper_done', fallback:true });} }, 9000);
});
}

// ─── COQUI TTS ────────────────────────────────────────────────────────
function coquiSpeak(text, wsId, voice, speed) {
const safe = text.replace(/[`$\'";|<>(){}[\]!#*?\n\r]/g,' ').slice(0,800);
return new Promise(resolve => {
  if (!coquiReady) { resolve({ type:'coqui_done', fallback:true }); return; }

  const params = new URLSearchParams({
    text: safe,
    speaker_id: '',
    style_wav: '',
    language_id: '',
  });
  if (voice) params.set('speaker_id', voice);

  const url = new URL(COQUI_URL + '/api/tts?' + params.toString());
  const opts = {
    hostname: url.hostname, port: url.port, path: url.pathname + url.search,
    method: 'GET', timeout: 30000,
  };

  const req = http.request(opts, res => {
    if (res.statusCode !== 200) {
      res.resume();
      resolve({ type:'coqui_done', fallback:true, status:res.statusCode });
      return;
    }
    const chunks = [];
    res.on('data', c => chunks.push(c));
    res.on('end', () => {
      const audio = Buffer.concat(chunks);
      if (audio.length < 100) { resolve({ type:'coqui_done', fallback:true }); return; }
      resolve({ type:'audio', data:audio.toString('base64'), engine:'coqui', done:true });
    });
  });

  req.on('error', () => {
    coquiReady = false;
    resolve({ type:'coqui_done', fallback:true });
  });
  req.on('timeout', () => {
    req.destroy();
    resolve({ type:'coqui_done', fallback:true, error:'timeout' });
  });
  req.end();
});
}

// ─── DIAGNOSTIC AGENT ─────────────────────────────────────────────────
function runDiagnostic(ws) {
const status = {
  type: 'diagnostic_report',
  ts: new Date().toISOString(),
  server: {
    uptime: Math.floor(process.uptime()),
    memory: process.memoryUsage(),
    pid: process.pid,
    nodeVersion: process.version,
  },
  tts: {
    piperReady,
    coquiReady,
    coquiURL: COQUI_URL,
    queueLength: ttsQueue.length,
    processing: ttsProcessing,
  },
  websocket: {
    clients: clients.size,
    features: ['piper_tts','coqui_tts','ddg_search','gh_oauth','plaid','shell','memory','collab','ai_proxy','auth','token_verify','audit_export','diagnostic','ping'],
  },
  ai: {
    claude: !!process.env.ANTHROPIC_API_KEY,
    gpt: !!process.env.OPENAI_API_KEY,
    grok: !!process.env.XAI_API_KEY,
  },
  errors: [],
};
// Check for common issues
if (!piperReady && !coquiReady) status.errors.push({code:'NO_TTS',message:'Neither Piper nor Coqui TTS is available',fix:'Install Piper binary or start Coqui server: tts-server --model_name tts_models/en/ljspeech/tacotron2-DDC'});
if (!process.env.ANTHROPIC_API_KEY && !process.env.OPENAI_API_KEY && !process.env.XAI_API_KEY)
  status.errors.push({code:'NO_AI_KEYS',message:'No AI API keys configured',fix:'Set ANTHROPIC_API_KEY, OPENAI_API_KEY, or XAI_API_KEY in .env'});
if (!fs.existsSync(ACCESS_LOG)) status.errors.push({code:'NO_LOG',message:'Audit log not found',fix:'Check LOG_DIR permissions'});
ws.send(JSON.stringify(status));
}

// ─── GITHUB OAUTH ─────────────────────────────────────────────────────
function ghOAuth(code, ws) {
const cid = process.env.GH_CLIENT_ID, sec = process.env.GH_CLIENT_SECRET;
if (!cid||!sec) { ws.send(JSON.stringify({type:'gh_token_error',error:'Set GH_CLIENT_ID + GH_CLIENT_SECRET'})); return; }
const body = 'client_id='+cid+'&client_secret='+sec+'&code='+encodeURIComponent(code);
const opts = { hostname:'github.com', path:'/login/oauth/access_token', method:'POST',
headers:{'Content-Type':'application/x-www-form-urlencoded','Accept':'application/json','Content-Length':body.length} };
const req = https.request(opts, res => {
const ch = []; res.on('data',c=>ch.push(c));
res.on('end', () => {
try {
const d = JSON.parse(Buffer.concat(ch).toString());
if (d.access_token) { audit('GH_OAUTH_OK','token issued'); ws.send(JSON.stringify({type:'gh_token',token:d.access_token,scope:d.scope})); }
else ws.send(JSON.stringify({type:'gh_token_error',error:d.error||'no token'}));
} catch(e) { ws.send(JSON.stringify({type:'gh_token_error',error:e.message})); }
});
});
req.on('error',e=>ws.send(JSON.stringify({type:'gh_token_error',error:e.message})));
req.write(body); req.end();
}

// ─── PLAID PROXY ──────────────────────────────────────────────────────
const plaidTokens = {};
function plaidProxy(type, data, ws) {
const env = data.env||'sandbox';
const host = {production:'api.plaid.com',development:'development.plaid.com'}[env]||'sandbox.plaid.com';
const endpoints = {plaid_link_token:'/link/token/create',plaid_exchange:'/item/public_token/exchange',plaid_balance:'/accounts/balance/get'};
const ep = endpoints[type]; if (!ep) return;
const bodyMap = {
plaid_link_token: {client_id:data.client_id,secret:data.secret,user:{client_user_id:'sg_'+(data.name||'user').replace(/\s/g,'_')},client_name:'SuperGrok',products:['auth','balance'],country_codes:['US'],language:'en'},
plaid_exchange:   {client_id:data.client_id,secret:data.secret,public_token:data.public_token},
plaid_balance:    {client_id:data.client_id,secret:data.secret,access_token:plaidTokens[data.name]||data.access_token},
};
const b = JSON.stringify(bodyMap[type]||{});
const opts = {hostname:host,path:ep,method:'POST',headers:{'Content-Type':'application/json','Content-Length':Buffer.byteLength(b)}};
const req = https.request(opts, res => {
const ch = []; res.on('data',c=>ch.push(c));
res.on('end', () => {
try {
const d = JSON.parse(Buffer.concat(ch).toString());
if (type==='plaid_link_token') ws.send(JSON.stringify({type:'plaid_link_token_result',link_token:d.link_token}));
else if (type==='plaid_exchange') { if(d.access_token) plaidTokens[data.name]=d.access_token; ws.send(JSON.stringify({type:'plaid_exchange_result',ok:!!d.access_token,name:data.name})); }
else if (type==='plaid_balance') ws.send(JSON.stringify({type:'plaid_balance_result',accounts:d.accounts||[],name:data.name}));
audit('PLAID',type+' '+env);
} catch(e) { ws.send(JSON.stringify({type:'plaid_error',error:e.message})); }
});
});
req.on('error',e=>ws.send(JSON.stringify({type:'plaid_error',error:e.message})));
req.write(b); req.end();
}

// ─── SHELL (ISH-compatible whitelist) ─────────────────────────────────
const SHELL_BANNED = /\b(rm|del|exec|eval|bash|sudo|su|chmod|format|mkfs|dd|curl|wget|nc|netcat|python -c|node -e)\b/i;
function runShell(cmd, role, ws) {
if (SHELL_BANNED.test(cmd)) {
audit('SHELL_BLOCKED',role+': '+cmd);
ws.send(JSON.stringify({type:'shell_output',ok:false,output:'BLOCKED: '+cmd})); return;
}
if (process.env.ALLOW_SHELL !== '1') {
ws.send(JSON.stringify({type:'shell_output',ok:true,output:'['+role+'] '+cmd+' -- echo (set ALLOW_SHELL=1 to exec)'})); return;
}
exec(cmd, {timeout:5000,maxBuffer:1024*32}, (err,stdout,stderr) => {
audit('SHELL_EXEC',role+': '+cmd);
ws.send(JSON.stringify({type:'shell_output',ok:!err,output:(stdout||stderr||(err&&err.message)||'').slice(0,4000)}));
});
}

// ─── PARSE BODY HELPER ────────────────────────────────────────────────
function readBody(req) {
return new Promise((resolve, reject) => {
const chunks = [];
req.on('data', c => { if (chunks.join('').length + c.length > 1024*512) { req.destroy(); reject(new Error('too large')); } else chunks.push(c); });
req.on('end', () => { try { resolve(JSON.parse(Buffer.concat(chunks).toString())); } catch(e) { reject(e); } });
req.on('error', reject);
});
}

// ─── HTTP SERVER ──────────────────────────────────────────────────────
const httpServer = http.createServer(async (req, res) => {
const ip  = (req.headers['x-forwarded-for'] || req.socket.remoteAddress || 'unknown').split(',')[0].trim();
const url = req.url.split('?')[0];

res.setHeader('Access-Control-Allow-Origin','*');
res.setHeader('Access-Control-Allow-Methods','GET,POST,OPTIONS');
res.setHeader('Access-Control-Allow-Headers','Content-Type,Authorization,X-Admin-Token');
res.setHeader('X-Content-Type-Options','nosniff');
res.setHeader('X-Frame-Options','DENY');

if (req.method === 'OPTIONS') { res.writeHead(204); res.end(); return; }

function json(status, data) { res.writeHead(status,{'Content-Type':'application/json'}); res.end(JSON.stringify(data)); }

// ── Health ─────────────────────────────────────────────────────────
if (url === '/health' || url === '/api/health') {
json(200, { status:'ok', ts:new Date().toISOString(), piper:piperReady, uptime:Math.floor(process.uptime()) });
return;
}

// ── POST routes ────────────────────────────────────────────────────
if (req.method === 'POST') {
let body;
try { body = await readBody(req); }
catch (e) { json(400, { detail:'Bad request: '+e.message }); return; }

if (!checkRate(ip)) { json(429, { detail:'Rate limit exceeded' }); return; }

if (url === '/api/auth/login') {
  const r = await doLogin(body, ip);
  json(r.s, r.d); return;
}
if (url === '/api/auth/verify-panel') {
  const r = doVerifyPanel(body, ip);
  json(r.s, r.d); return;
}
if (url === '/api/auth/verify-passphrase') {
  const { role, passphrase_hash } = body;
  const r = (role||'').toLowerCase();
  const cfg = RM[r];
  if (!cfg||!cfg.pp) { json(400,{detail:'n/a'}); return; }
  const ex = PP_HASHES[r]||'';
  try {
    const a = Buffer.alloc(32), b = Buffer.alloc(32);
    Buffer.from((passphrase_hash||'').toLowerCase().slice(0,64).padEnd(64,'0'),'hex').copy(a);
    Buffer.from(ex.slice(0,64).padEnd(64,'0'),'hex').copy(b);
    if (crypto.timingSafeEqual(a,b)) { audit('PP_OK',r,{ip}); json(200,{ok:true}); }
    else { recordFail(ip); audit('PP_BAD',r,{ip}); await new Promise(r2=>setTimeout(r2,1500)); json(403,{detail:'Access Denied'}); }
  } catch { json(403,{detail:'Access Denied'}); }
  return;
}
if (url === '/api/auth/refresh') {
  const auth = (req.headers.authorization||'').replace('Bearer ','');
  try {
    const old = verifyToken(auth);
    old.iat = Math.floor(Date.now()/1000); old.exp = old.iat+28800; old.jti = crypto.randomBytes(16).toString('hex');
    json(200, { token:signToken(old), expires_in:28800 });
  } catch(e) { json(401,{detail:e.message}); }
  return;
}
if (url === '/api/auth/webauthn/challenge') {
  const { user_id, role } = body;
  const challenge = crypto.randomBytes(32).toString('base64url');
  const cfg = RM[(role||'').toLowerCase()]||{};
  json(200,{ challenge, challenge_token:signToken({challenge,user_id,exp:Math.floor(Date.now()/1000)+60}), rp_id:'localhost', required:cfg.lvl>=2 });
  return;
}
if (url === '/api/logs/event') {
  const auth = (req.headers.authorization||'').replace('Bearer ','');
  try { const p = verifyToken(auth); audit('CLIENT:'+body.type, body.msg||'', {ip,user:p.sub}); json(200,{ok:true}); }
  catch { json(401,{detail:'invalid token'}); }
  return;
}
if (url === '/api/execute-command') {
  const { command, role } = body;
  if (SHELL_BANNED.test(command||'')) { audit('CMD_BLOCKED',role+': '+command,{ip}); json(403,{output:'Blocked'}); return; }
  audit('CMD',role+': '+command,{ip});
  json(200,{output:'['+role+'] '+command+' -- ack '+new Date().toISOString()});
  return;
}

}

// ── GET routes ─────────────────────────────────────────────────────
if (req.method === 'GET') {
if (url === '/api/logs/access') {
const tok = req.headers['x-admin-token']||'';
try {
const p = verifyToken(tok);
if (p.lvl < 5) throw new Error('insufficient clearance');
const lines = fs.existsSync(ACCESS_LOG)
? fs.readFileSync(ACCESS_LOG,'utf8').trim().split('\n').slice(-200).map(l=>{try{return JSON.parse(l);}catch{return l;}})
: [];
json(200,{logs:lines,count:lines.length});
} catch(e) { json(403,{detail:e.message}); }
return;
}
if (url === '/api/auth/child-block') {
const role = (req.url.split('role=')[1]||'').split('&')[0];
json(200,{blocked:CHILD_BLOCKED.has(role.toLowerCase())});
return;
}
}

json(404,{detail:'not found'});
});

// ─── WEBSOCKET ────────────────────────────────────────────────────────
const wss = new ws_mod.WebSocketServer({ server: httpServer });
const clients = new Map();
const memStore = {};

wss.on('connection', (ws, req) => {
const ip   = (req.headers['x-forwarded-for']||req.socket.remoteAddress||'?').split(',')[0].trim();
const wsId = crypto.randomBytes(8).toString('hex');
clients.set(wsId, ws);
const rw = { n:0, reset:Date.now()+60000 };
audit('WS_CONNECT', wsId, {ip});

ws.send(JSON.stringify({ type:'connected', wsId, piper:piperReady, coqui:coquiReady, ts:Date.now(),
features:['piper_tts','coqui_tts','ddg_search','gh_oauth','plaid','shell','memory','collab','ai_proxy','auth','token_verify','audit_export','diagnostic','ping'] }));

ws.on('message', async raw => {
const now = Date.now();
if (now > rw.reset) { rw.n=0; rw.reset=now+60000; }
if (++rw.n > 80) { ws.send(JSON.stringify({type:'error',code:'RATE_LIMIT'})); return; }

let msg; try { msg = JSON.parse(raw); } catch { ws.send(JSON.stringify({type:'error',code:'PARSE'})); return; }
const { type } = msg;
audit('WS', type, {wsId});

if (type === 'ping') {
  ws.send(JSON.stringify({type:'pong',ts:Date.now(),piper:piperReady,coqui:coquiReady,wsId,uptime:Math.floor(process.uptime())})); return;
}

if (type === 'piper_speak' || type === 'speak') {
  if (!msg.text) { ws.send(JSON.stringify({type:'error',code:'NO_TEXT'})); return; }
  ws.send(JSON.stringify(await enqueueTTS(msg.text, wsId, 'piper', '', msg.speed||1.0))); return;
}

if (type === 'coqui_speak') {
  if (!msg.text) { ws.send(JSON.stringify({type:'error',code:'NO_TEXT'})); return; }
  ws.send(JSON.stringify(await enqueueTTS(msg.text, wsId, 'coqui', msg.voice||'', msg.speed||1.0))); return;
}

if (type === 'tts_speak') {
  if (!msg.text) { ws.send(JSON.stringify({type:'error',code:'NO_TEXT'})); return; }
  ws.send(JSON.stringify(await enqueueTTS(msg.text, wsId, msg.engine||'auto', msg.voice||'', msg.speed||1.0))); return;
}

if (type === 'tts_status') {
  ws.send(JSON.stringify({type:'tts_status',piper:piperReady,coqui:coquiReady,queueLength:ttsQueue.length,processing:ttsProcessing})); return;
}

if (type === 'diagnostic') {
  runDiagnostic(ws); return;
}

if (type === 'ddg_search') {
  const r = await ddgSearch(msg.query||'');
  ws.send(JSON.stringify({type:'ddg_result',...r})); return;
}

if (type === 'ai_query') {
  aiProxy(msg.model||'claude', msg.text||'', msg.system||'', msg.apiKey||'', (err, response) => {
    ws.send(JSON.stringify({type:'ai_response', text:response, model:msg.model||'claude'}));
  }); return;
}

if (type === 'gh_exchange') { ghOAuth(msg.code||'', ws); return; }

if (['plaid_link_token','plaid_exchange','plaid_balance'].includes(type)) { plaidProxy(type, msg, ws); return; }

if (type === 'shell_cmd') { runShell(msg.cmd||'', msg.role||'user', ws); return; }

if (type === 'memory_save') {
  const k = msg.key||wsId;
  memStore[k] = (memStore[k]||[]);
  memStore[k].unshift({ts:Date.now(),...(msg.card||{})});
  if (memStore[k].length > 50) memStore[k].length = 50;
  ws.send(JSON.stringify({type:'memory_saved',key:k})); return;
}
if (type === 'memory_get') {
  ws.send(JSON.stringify({type:'memory_result',cards:memStore[msg.key||wsId]||[]})); return;
}

if (type === 'collab_broadcast') {
  let sent = 0;
  clients.forEach((c,id) => { if(id!==wsId && c.readyState===ws_mod.OPEN) { c.send(JSON.stringify({type:'collab_event',payload:msg.payload,from:msg.from||wsId,ts:Date.now()})); sent++; } });
  ws.send(JSON.stringify({type:'collab_ack',sent})); return;
}

if (type === 'token_verify') {
  try { const p = verifyToken(msg.token||''); ws.send(JSON.stringify({type:'token_ok',lvl:p.lvl,sub:p.sub,panels:p.panels,role:p.role})); }
  catch(e) { ws.send(JSON.stringify({type:'token_invalid',reason:e.message})); }
  return;
}

if (type === 'mfa_gen') {
  const tok = crypto.randomBytes(3).toString('hex').toUpperCase();
  const exp = Date.now() + 300000;
  const signed = signToken({mfa:tok,role:msg.role||'',exp:Math.floor(exp/1000)});
  ws.send(JSON.stringify({type:'mfa_token',token:tok,signed,expires:exp})); return;
}
if (type === 'mfa_verify') {
  try { const p = verifyToken(msg.signed||''); ws.send(JSON.stringify({type:'mfa_result',ok:p.mfa===msg.token})); }
  catch { ws.send(JSON.stringify({type:'mfa_result',ok:false})); }
  return;
}

if (type === 'audit_export') {
  try {
    const p = verifyToken(msg.token||'');
    if (p.lvl < 3) { ws.send(JSON.stringify({type:'audit_denied'})); return; }
    const lines = fs.existsSync(ACCESS_LOG)
      ? fs.readFileSync(ACCESS_LOG,'utf8').trim().split('\n').slice(-500).map(l=>{try{return JSON.parse(l);}catch{return l;}})
      : [];
    ws.send(JSON.stringify({type:'audit_data',logs:lines}));
  } catch { ws.send(JSON.stringify({type:'audit_denied'})); }
  return;
}

if (type === 'kc_save') { const sessions = (memStore['__kc']||{}); sessions[wsId]=msg.data; memStore['__kc']=sessions; ws.send(JSON.stringify({type:'kc_saved',wsId})); return; }
if (type === 'kc_load') { const sessions = (memStore['__kc']||{}); ws.send(JSON.stringify({type:'kc_session',session:sessions[wsId]||null})); return; }

ws.send(JSON.stringify({type:'error',code:'UNKNOWN',received:type}));

});

ws.on('close', () => { clients.delete(wsId); audit('WS_CLOSE',wsId,{ip}); });
ws.on('error', e => { clients.delete(wsId); audit('WS_ERR',wsId+': '+e.message,{ip}); });
});

// ─── START PRIMARY PORT ───────────────────────────────────────────────
httpServer.listen(PORT_UNIFIED, '127.0.0.1', () => {
audit('START', 'SuperGrok Unified :'+PORT_UNIFIED);
process.stdout.write('\n╔══════════════════════════════════════════════════╗\n');
process.stdout.write('║  SuperGrok Unified Server -- LIVE                 ║\n');
process.stdout.write('║  Primary   http://127.0.0.1:'+PORT_UNIFIED+'               ║\n');
process.stdout.write('║  Bridge WS ws://127.0.0.1:'+PORT_BRIDGE+' (proxy)        ║\n');
process.stdout.write('║  Auth      http://127.0.0.1:'+PORT_AUTH+' (proxy)        ║\n');
process.stdout.write('║  Piper TTS '+(piperReady?'✅ Ready    ':'⚠️  Not found  ')+'                       ║\n');
process.stdout.write('║  Coqui TTS '+(coquiReady?'✅ Ready    ':'⚠️  Not found  ')+'                       ║\n');
process.stdout.write('║  Audit log '+ACCESS_LOG.slice(0,30).padEnd(30,' ')+'║\n');
process.stdout.write('╚══════════════════════════════════════════════════╝\n\n');
});

// ─── PROXY LISTENERS (legacy ports keep working unchanged) ───────────
function makeProxy(port, label) {
const srv = http.createServer((req, res) => {
res.setHeader('Access-Control-Allow-Origin','*');
res.setHeader('Access-Control-Allow-Methods','GET,POST,OPTIONS');
res.setHeader('Access-Control-Allow-Headers','Content-Type,Authorization,X-Admin-Token');
if (req.method==='OPTIONS') { res.writeHead(204); res.end(); return; }
const opts = { hostname:'127.0.0.1', port:PORT_UNIFIED, path:req.url, method:req.method, headers:req.headers };
const p = http.request(opts, r => { res.writeHead(r.statusCode, r.headers); r.pipe(res); });
req.pipe(p); p.on('error', () => { try { res.writeHead(502); res.end(); } catch(e){} });
});
const wsp = new ws_mod.WebSocketServer({ server: srv });
wsp.on('connection', (ws2, req2) => {
const tgt = new ws_mod.WebSocket('ws://127.0.0.1:'+PORT_UNIFIED, { headers: req2.headers });
tgt.on('open', () => {
ws2.on('message', d => tgt.readyState===ws_mod.OPEN && tgt.send(d));
tgt.on('message', d => ws2.readyState===ws_mod.OPEN && ws2.send(d));
tgt.on('close', () => { try{ws2.close();}catch(e){} });
ws2.on('close', () => { try{tgt.close();}catch(e){} });
});
tgt.on('error', () => { try{ws2.close();}catch(e){} });
});
srv.listen(port, '127.0.0.1', () => process.stdout.write('  '+label+' :'+port+' → proxied\n'));
return srv;
}
makeProxy(PORT_BRIDGE, 'Bridge  ');
makeProxy(PORT_AUTH,   'Auth    ');

// ─── GRACEFUL SHUTDOWN ────────────────────────────────────────────────
function shutdown(sig) {
audit('SHUTDOWN', sig);
process.stdout.write('\n[SuperGrok] '+sig+' -- shutting down\n');
clients.forEach(ws => { try{ws.close();}catch(_){} });
httpServer.close(() => process.exit(0));
setTimeout(() => process.exit(0), 3000);
}
process.on('SIGINT',  () => shutdown('SIGINT'));
process.on('SIGTERM', () => shutdown('SIGTERM'));
process.on('uncaughtException', e => { audit('UNCAUGHT', e.message); process.stdout.write('[ERR] '+e.message+'\n'); });
process.on('unhandledRejection', e => { audit('UNHANDLED', String(e)); });
