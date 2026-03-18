/**

- SuperGrok v82 — Bridge Git Handler
- Add this block to Unified_Server.js inside the WebSocket message handler
- (where existing cases like ‘ai_query’, ‘ping’, etc. are handled)
- 
- Handles: git_push, git_status, key_rotate, memory_sync, agent_status_request
  */

// ── Inside your ws.on(‘message’, async (raw) => { switch(msg.type) { … }) ──

case ‘git_push’: {
const { exec } = require(‘child_process’);
const remote  = (msg.remote||’’).replace(/[^a-zA-Z0-9@:./*-]/g,’’);
const branch  = (msg.branch||‘main’).replace(/[^a-zA-Z0-9/*-]/g,’’);
const message = (msg.message||‘chore: SuperGrok update’).replace(/[”`$\\]/g,' '); if (!remote) { ws.send(JSON.stringify({type:'git_push_result',success:false,message:'No remote'})); break; } const cmd = `git add -A && git commit -m “${message}” –allow-empty && git push “${remote}” ${branch}`;
exec(cmd, {timeout:30000}, (err,stdout,stderr) => {
ws.send(JSON.stringify({
type:‘git_push_result’,
success:!err,
repo: msg.repo||remote,
output:(stdout||’’)+(stderr||’’)+(err?’\nERR: ‘+err.message:’’),
message: err ? err.message : ‘Pushed successfully’
}));
});
break;
}

case ‘git_status’: {
const { exec } = require(‘child_process’);
exec(‘git status –short && echo “—” && git log –oneline -5 && echo “—” && git remote -v’, {timeout:5000}, (err,stdout,stderr) => {
ws.send(JSON.stringify({type:‘git_status_result’,output:stdout||stderr||‘No output’,success:!err}));
});
break;
}

case ‘key_rotate’: {
// Rotate to next available API key from pool
const keys = {
anthropic: (process.env.ANTHROPIC_API_KEY_POOL||process.env.ANTHROPIC_API_KEY||’’).split(’,’).filter(Boolean),
openai:    (process.env.OPENAI_API_KEY_POOL||process.env.OPENAI_API_KEY||’’).split(’,’).filter(Boolean),
xai:       (process.env.XAI_API_KEY_POOL||process.env.XAI_API_KEY||’’).split(’,’).filter(Boolean),
};
let rotated = false;
Object.keys(keys).forEach(provider => {
if(keys[provider].length > 1) {
// Rotate: move head to tail
const k = keys[provider].shift();
keys[provider].push(k);
// Update active key in process.env
if(provider===‘anthropic’) process.env.ANTHROPIC_API_KEY = keys[provider][0];
if(provider===‘openai’)    process.env.OPENAI_API_KEY    = keys[provider][0];
if(provider===‘xai’)       process.env.XAI_API_KEY       = keys[provider][0];
rotated = true;
}
});
ws.send(JSON.stringify({type:‘key_rotated’,rotated,reason:msg.reason||‘manual’,ts:Date.now()}));
break;
}

case ‘memory_sync’: {
// Store memory cards server-side (append to session log)
const fs = require(‘fs’);
const path = require(‘path’);
const logDir = process.env.LOG_DIR || ‘./logs’;
if(!fs.existsSync(logDir)) fs.mkdirSync(logDir,{recursive:true});
const memLog = path.join(logDir, ‘memory_sync.jsonl’);
const cards = Array.isArray(msg.cards) ? msg.cards.slice(0,50) : [];
cards.forEach(c => {
try { fs.appendFileSync(memLog, JSON.stringify({…c, bridge_ts: Date.now()})+’\n’); } catch(e){}
});
ws.send(JSON.stringify({type:‘memory_saved’,count:cards.length,ts:Date.now()}));
break;
}

case ‘agent_status_request’: {
// Report which agent backends are configured
const statuses = {
claude:  !!process.env.ANTHROPIC_API_KEY  ? ‘online’ : ‘offline’,
gpt:     !!process.env.OPENAI_API_KEY     ? ‘online’ : ‘offline’,
grok:    !!process.env.XAI_API_KEY        ? ‘online’ : ‘offline’,
copilot: !!process.env.GITHUB_COPILOT_TOKEN ? ‘online’ : ‘offline’,
watcher: ‘online’,
};
Object.keys(statuses).forEach(agent => {
ws.send(JSON.stringify({type:‘agent_status’,agent,status:statuses[agent]}));
});
break;
}
