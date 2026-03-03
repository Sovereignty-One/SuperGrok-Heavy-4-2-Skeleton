/**
 * SuperGrok AI Platform — Bridge Server (Port 9898)
 *
 * Provides the local backend for Global_Roles_Dashboard.html:
 *   GET  /health                   – health check
 *   POST /api/ai/chat              – AI proxy (Claude / GPT-4o / Grok)
 *   POST /api/execute-command      – safe terminal command execution
 *   GET  /api/memory               – list persisted memory entries
 *   POST /api/memory               – add a memory entry
 *   DELETE /api/memory/:id         – remove a memory entry
 *   GET  /api/audit                – list audit log entries
 *   POST /api/audit                – append an audit entry
 *   WS   ws://localhost:9898       – real-time channel
 *     → ping                       – responds with pong
 *     → ai_query                   – proxy AI request, stream reply back
 *     → piper_speak                – synthesise speech via Piper TTS
 *
 * Environment variables (all optional – keys enable live AI):
 *   PORT              server port (default 9898)
 *   ANTHROPIC_API_KEY Claude key  (sk-ant-…)
 *   OPENAI_API_KEY    OpenAI key  (sk-…)
 *   XAI_API_KEY       xAI key
 *   PIPER_BIN         path to piper binary (default: piper)
 *   DATA_DIR          directory for JSON data files (default: ./data)
 *   TLS_CERT          path to PEM certificate for HTTPS/WSS
 *   TLS_KEY           path to PEM private key for HTTPS/WSS
 *
 * Usage:
 *   node server_9898.js
 *   TLS_CERT=cert.pem TLS_KEY=key.pem node server_9898.js
 */

'use strict';

const http  = require('http');
const https = require('https');
const fs    = require('fs');
const path  = require('path');
const cp    = require('child_process');
const { URL } = require('url');

// ---------------------------------------------------------------------------
// Config
// ---------------------------------------------------------------------------
const PORT      = parseInt(process.env.PORT || '9898', 10);
const DATA_DIR  = process.env.DATA_DIR || path.join(__dirname, 'data');
const PIPER_BIN = process.env.PIPER_BIN || 'piper';

const ANTHROPIC_KEY = process.env.ANTHROPIC_API_KEY || '';
const OPENAI_KEY    = process.env.OPENAI_API_KEY    || '';
const XAI_KEY       = process.env.XAI_API_KEY       || '';

// ---------------------------------------------------------------------------
// Data persistence helpers
// ---------------------------------------------------------------------------
function ensureDataDir() {
  if (!fs.existsSync(DATA_DIR)) fs.mkdirSync(DATA_DIR, { recursive: true });
}

function readJSON(name, fallback) {
  ensureDataDir();
  const file = path.join(DATA_DIR, name);
  try { return JSON.parse(fs.readFileSync(file, 'utf8')); }
  catch (e) { /* File missing or invalid JSON — return fallback */ return fallback; }
}

function writeJSON(name, data) {
  ensureDataDir();
  fs.writeFileSync(path.join(DATA_DIR, name), JSON.stringify(data, null, 2));
}

// ---------------------------------------------------------------------------
// Tiny HTTP helper — make a JSON request to an external API
// ---------------------------------------------------------------------------
function apiPost(url, headers, body) {
  return new Promise((resolve, reject) => {
    const parsed = new URL(url);
    const isHttps = parsed.protocol === 'https:';
    const transport = isHttps ? https : http;
    const payload = JSON.stringify(body);
    const opts = {
      hostname: parsed.hostname,
      port:     parsed.port || (isHttps ? 443 : 80),
      path:     parsed.pathname + parsed.search,
      method:   'POST',
      headers:  {
        'Content-Type':   'application/json',
        'Content-Length': Buffer.byteLength(payload),
        ...headers,
      },
    };
    const req = transport.request(opts, (res) => {
      let raw = '';
      res.on('data', (c) => (raw += c));
      res.on('end', () => {
        try { resolve({ status: res.statusCode, body: JSON.parse(raw) }); }
        catch (e) { resolve({ status: res.statusCode, body: raw }); }
      });
    });
    req.on('error', reject);
    req.write(payload);
    req.end();
  });
}

// ---------------------------------------------------------------------------
// AI proxy — calls Anthropic / OpenAI / xAI depending on model
// ---------------------------------------------------------------------------
async function callAI(model, system, messages) {
  if (model === 'claude') {
    const key = ANTHROPIC_KEY;
    if (!key) return { error: 'ANTHROPIC_API_KEY not set on bridge server' };
    const r = await apiPost(
      'https://api.anthropic.com/v1/messages',
      { 'x-api-key': key, 'anthropic-version': '2023-06-01' },
      { model: 'claude-sonnet-4-20250514', max_tokens: 1200, system, messages },
    );
    if (r.body && r.body.content && r.body.content[0]) {
      return { text: r.body.content[0].text };
    }
    return { error: r.body && r.body.error ? r.body.error.message : 'Claude API error', status: r.status };
  }

  if (model === 'gpt') {
    const key = OPENAI_KEY;
    if (!key) return { error: 'OPENAI_API_KEY not set on bridge server' };
    const r = await apiPost(
      'https://api.openai.com/v1/chat/completions',
      { Authorization: `Bearer ${key}` },
      { model: 'gpt-4o', max_tokens: 1200, messages: [{ role: 'system', content: system }, ...messages] },
    );
    if (r.body && r.body.choices && r.body.choices[0]) {
      return { text: r.body.choices[0].message.content };
    }
    return { error: r.body && r.body.error ? r.body.error.message : 'OpenAI API error', status: r.status };
  }

  if (model === 'grok') {
    const key = XAI_KEY;
    if (!key) return { error: 'XAI_API_KEY not set on bridge server' };
    const r = await apiPost(
      'https://api.x.ai/v1/chat/completions',
      { Authorization: `Bearer ${key}` },
      { model: 'grok-2-latest', max_tokens: 1200, messages: [{ role: 'system', content: system }, ...messages] },
    );
    if (r.body && r.body.choices && r.body.choices[0]) {
      return { text: r.body.choices[0].message.content };
    }
    return { error: 'Grok API error', status: r.status };
  }

  return { error: `Unknown model: ${model}` };
}

// ---------------------------------------------------------------------------
// Safe command execution — allowlist only
// ---------------------------------------------------------------------------
const SAFE_CMDS = new Set([
  'pwd', 'ls', 'date', 'whoami', 'hostname', 'uname',
  'node --version', 'npm --version', 'python3 --version', 'python --version',
  'echo', 'cat', 'head', 'tail', 'wc',
]);

function isSafeCommand(cmd) {
  const base = cmd.trim().split(/\s+/)[0];
  if (SAFE_CMDS.has(cmd.trim())) return true;
  if (['echo', 'cat', 'head', 'tail', 'wc', 'ls'].includes(base)) return true;
  return false;
}

function executeCommand(cmd, role) {
  if (!isSafeCommand(cmd)) {
    return { output: `[Bridge] Command restricted for role ${role || 'user'}: ${cmd}\nAllowed: pwd, ls, date, whoami, node --version, etc.`, exit: 1 };
  }
  try {
    const out = cp.execSync(cmd, { timeout: 5000, encoding: 'utf8', shell: '/bin/sh' });
    return { output: out, exit: 0 };
  } catch (e) {
    return { output: e.message, exit: e.status || 1 };
  }
}

// ---------------------------------------------------------------------------
// Piper TTS
// ---------------------------------------------------------------------------
function piperSpeak(text, ws) {
  const clean = text.replace(/[<>]/g, '').slice(0, 500);
  try {
    const proc = cp.spawn(PIPER_BIN, ['--output-raw'], { stdio: ['pipe', 'pipe', 'ignore'] });
    const chunks = [];
    proc.stdin.write(clean);
    proc.stdin.end();
    proc.stdout.on('data', (c) => chunks.push(c));
    proc.stdout.on('end', () => {
      if (ws.readyState === 1) {
        ws.send(JSON.stringify({ type: 'audio', data: Buffer.concat(chunks).toString('base64') }));
      }
    });
    proc.on('error', () => { /* piper binary not installed — skip */ });
  } catch (e) { /* piper not installed — skip */ }
}

// ---------------------------------------------------------------------------
// HTTP request router
// ---------------------------------------------------------------------------
function readBody(req) {
  return new Promise((resolve) => {
    let raw = '';
    req.on('data', (c) => (raw += c));
    req.on('end', () => {
      try { resolve(JSON.parse(raw)); } catch (e) { /* Invalid JSON body — return empty object */ resolve({}); }
    });
  });
}

function respond(res, status, body) {
  const payload = JSON.stringify(body);
  res.writeHead(status, {
    'Content-Type':                'application/json',
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'GET,POST,DELETE,OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type,Authorization',
  });
  res.end(payload);
}

async function handleRequest(req, res) {
  // CORS preflight
  if (req.method === 'OPTIONS') {
    res.writeHead(204, {
      'Access-Control-Allow-Origin':  '*',
      'Access-Control-Allow-Methods': 'GET,POST,DELETE,OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type,Authorization',
    });
    return res.end();
  }

  const urlObj = new URL(req.url, `http://localhost`);
  const urlPath = urlObj.pathname;
  const method  = req.method;

  // GET /health
  if (method === 'GET' && urlPath === '/health') {
    return respond(res, 200, {
      status:    'healthy',
      service:   'server_9898',
      uptime:    process.uptime(),
      ai:        { claude: !!ANTHROPIC_KEY, gpt: !!OPENAI_KEY, grok: !!XAI_KEY },
      timestamp: new Date().toISOString(),
    });
  }

  // POST /api/ai/chat
  if (method === 'POST' && urlPath === '/api/ai/chat') {
    const body = await readBody(req);
    const { model = 'claude', system = '', messages = [], text } = body;
    const msgs = messages.length ? messages : [{ role: 'user', content: text || '' }];
    const result = await callAI(model, system, msgs);
    return respond(res, result.error ? 502 : 200, result);
  }

  // POST /api/execute-command
  if (method === 'POST' && urlPath === '/api/execute-command') {
    const body = await readBody(req);
    const { command = '', role = 'user' } = body;
    const result = executeCommand(command, role);
    return respond(res, 200, result);
  }

  // GET /api/memory
  if (method === 'GET' && urlPath === '/api/memory') {
    return respond(res, 200, readJSON('memory.json', []));
  }

  // POST /api/memory
  if (method === 'POST' && urlPath === '/api/memory') {
    const body  = await readBody(req);
    const items = readJSON('memory.json', []);
    const entry = {
      id:      Date.now().toString(36) + Math.random().toString(36).slice(2, 6),
      title:   (body.title  || 'Note').slice(0, 200),
      content: (body.content || '').slice(0, 2000),
      ts:      new Date().toISOString(),
      auto:    !!body.auto,
    };
    items.push(entry);
    if (items.length > 200) items = items.slice(-200);
    writeJSON('memory.json', items);
    return respond(res, 201, entry);
  }

  // DELETE /api/memory/:id
  if (method === 'DELETE' && urlPath.startsWith('/api/memory/')) {
    const id    = urlPath.slice('/api/memory/'.length);
    const items = readJSON('memory.json', []);
    const next  = items.filter((e) => e.id !== id);
    writeJSON('memory.json', next);
    return respond(res, 200, { deleted: items.length - next.length });
  }

  // GET /api/audit
  if (method === 'GET' && urlPath === '/api/audit') {
    return respond(res, 200, readJSON('audit.json', []));
  }

  // POST /api/audit
  if (method === 'POST' && urlPath === '/api/audit') {
    const body    = await readBody(req);
    const entries = readJSON('audit.json', []);
    const entry   = {
      id:      Date.now().toString(36) + Math.random().toString(36).slice(2, 6),
      action:  (body.action  || 'EVENT').slice(0, 100),
      detail:  (body.detail  || '').slice(0, 500),
      role:    (body.role    || '').slice(0, 60),
      ts:      new Date().toISOString(),
    };
    entries.push(entry);
    if (entries.length > 1000) entries = entries.slice(-1000);
    writeJSON('audit.json', entries);
    return respond(res, 201, entry);
  }

  respond(res, 404, { error: 'Not found', path: urlPath });
}

// ---------------------------------------------------------------------------
// Build HTTP(S) server
// ---------------------------------------------------------------------------
let server;
if (process.env.TLS_CERT && process.env.TLS_KEY) {
  const tlsOpts = {
    cert: fs.readFileSync(process.env.TLS_CERT),
    key:  fs.readFileSync(process.env.TLS_KEY),
  };
  server = https.createServer(tlsOpts, handleRequest);
  console.log('[server_9898] TLS enabled');
} else {
  server = http.createServer(handleRequest);
}

// ---------------------------------------------------------------------------
// WebSocket server — accepts connections at any path (root ws://localhost:9898)
// ---------------------------------------------------------------------------
let wss = null;
try {
  const { WebSocketServer } = require('ws');
  wss = new WebSocketServer({ server });
  const clients = new Set();

  wss.on('connection', (ws) => {
    clients.add(ws);
    console.log(`[ws] client connected (${clients.size} total)`);

    ws.on('close', () => {
      clients.delete(ws);
      console.log(`[ws] client disconnected (${clients.size} total)`);
    });

    ws.on('message', async (raw) => {
      let msg;
      try { msg = JSON.parse(raw); } catch (e) { /* Malformed WebSocket message — ignore */ return; }

      switch (msg.type) {
        case 'ping':
          ws.send(JSON.stringify({ type: 'pong', timestamp: new Date().toISOString() }));
          break;

        case 'ai_query': {
          const { text = '', model = 'claude', system = '' } = msg;
          const result = await callAI(model, system, [{ role: 'user', content: text }]);
          if (ws.readyState === 1) {
            ws.send(JSON.stringify({
              type:  'ai_response',
              model,
              text:  result.text  || '',
              error: result.error || null,
            }));
          }
          break;
        }

        case 'piper_speak':
          if (msg.text) piperSpeak(msg.text, ws);
          break;

        default:
          break;
      }
    });
  });

  console.log('[server_9898] WebSocket support enabled');
} catch (e) {
  console.warn('[server_9898] WebSocket unavailable (install ws): ' + e.message);
}

// ---------------------------------------------------------------------------
// Start
// ---------------------------------------------------------------------------
if (require.main === module) {
  server.listen(PORT, () => {
    const proto = (process.env.TLS_CERT && process.env.TLS_KEY) ? 'wss' : 'ws';
    console.log(`[server_9898] listening on http://localhost:${PORT}`);
    console.log(`[server_9898] WebSocket   ${proto}://localhost:${PORT}`);
    console.log(`[server_9898] AI keys loaded: claude=${!!ANTHROPIC_KEY} gpt=${!!OPENAI_KEY} grok=${!!XAI_KEY}`);
    console.log(`[server_9898] Data dir: ${DATA_DIR}`);
  });
}

module.exports = { server, wss, callAI, executeCommand };
