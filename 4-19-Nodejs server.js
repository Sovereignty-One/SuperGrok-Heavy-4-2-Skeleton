// ============================================================
// SuperGrok Node.js WebSocket Bridge v1.0
// Port layout:
//   9899 ← this server (WebSocket + HTTP health)
//   9897 ← Python bridge upstream (HTTP POST dispatch)
//   9898 ← KODER app server (iOS file server)
//   8080/8443 ← Keycloak
//   5432 ← PostgreSQL
//   6379 ← Redis
//
// Run:  node server.js
// Deps: ws (npm install ws)  or use –no-external for stdlib WS
// ============================================================

‘use strict’;

const http   = require(‘http’);
const https  = require(‘https’);
require(‘dotenv’).config({ silent: true });

const BRIDGE_PORT   = parseInt(process.env.BRIDGE_PORT  || ‘9899’, 10);
const BRIDGE_HOST   = process.env.BRIDGE_HOST            || ‘0.0.0.0’;
const BACKEND_URL   = process.env.BACKEND_URL             || ‘http://127.0.0.1:9897’;
const BACKEND_TIMEOUT = parseInt(process.env.BACKEND_TIMEOUT_MS || ‘30000’, 10);
const PING_MS       = parseInt(process.env.PING_INTERVAL_MS || ‘25000’, 10);
const LOG_LEVEL     = process.env.LOG_LEVEL               || ‘info’;
const KC_URL        = process.env.KEYCLOAK_URL             || ‘http://127.0.0.1:8080’;

// ── Logger ────────────────────────────────────────────────────────────────
const log = {
info:  (…a) => console.log (’[BRIDGE]’,     new Date().toISOString(), …a),
warn:  (…a) => console.warn(’[BRIDGE:WARN]’, new Date().toISOString(), …a),
error: (…a) => console.error(’[BRIDGE:ERR]’, new Date().toISOString(), …a),
debug: (…a) => { if (LOG_LEVEL === ‘debug’) console.log(’[BRIDGE:DBG]’, …a); }
};

// ── HTTP POST → Python backend on 9897 ───────────────────────────────────
function dispatchToPython(payload) {
return new Promise((resolve, reject) => {
const body   = JSON.stringify(payload);
const parsed = new URL(BACKEND_URL + ‘/ws-dispatch’);
const lib    = parsed.protocol === ‘https:’ ? https : http;
const opts   = {
hostname: parsed.hostname,
port:     parsed.port || (parsed.protocol === ‘https:’ ? 443 : 9897),
path:     parsed.pathname,
method:   ‘POST’,
headers: {
‘Content-Type’:    ‘application/json’,
‘Content-Length’:  Buffer.byteLength(body),
‘X-Bridge-Source’: ‘node-bridge-9899’,
},
};
const req = lib.request(opts, (res) => {
let data = ‘’;
res.on(‘data’, (c) => { data += c; });
res.on(‘end’, () => {
if (res.statusCode >= 200 && res.statusCode < 300) {
try { resolve(JSON.parse(data)); }
catch { resolve({ type: ‘raw’, data }); }
} else {
reject(new Error(`Python ${res.statusCode}: ${data.slice(0, 200)}`));
}
});
});
req.setTimeout(BACKEND_TIMEOUT, () => req.destroy(new Error(‘Python timeout’)));
req.on(‘error’, reject);
req.write(body);
req.end();
});
}

// ── RFC 6455 minimal WebSocket (no external dep) ─────────────────────────
const WS_GUID = ‘258EAFA5-E914-47DA-95CA-C5AB0DC85B11’;
const crypto  = require(‘crypto’);

function wsAccept(key) {
return crypto.createHash(‘sha1’).update(key.trim() + WS_GUID).digest(‘base64’);
}

function wsSend(socket, payload) {
if (typeof payload === ‘object’) payload = JSON.stringify(payload);
const buf = Buffer.from(payload, ‘utf8’);
const len = buf.length;
let hdr;
if      (len < 126)   hdr = Buffer.from([0x81, len]);
else if (len < 65536) hdr = Buffer.from([0x81, 126, len >> 8, len & 0xFF]);
else {
hdr = Buffer.allocUnsafe(10);
hdr[0] = 0x81; hdr[1] = 127;
hdr.writeBigUInt64BE(BigInt(len), 2);
}
try { socket.write(Buffer.concat([hdr, buf])); }
catch(_e) {}
}

function wsRead(data) {
const frames = [];
let off = 0;
while (off < data.length) {
if (off + 2 > data.length) break;
const opcode = data[off] & 0x0F;
const fin    = !!(data[off] & 0x80);
const masked = !!(data[off + 1] & 0x80);
let plen = data[off + 1] & 0x7F;
off += 2;
if (plen === 126) { plen = data.readUInt16BE(off); off += 2; }
else if (plen === 127) { plen = Number(data.readBigUInt64BE(off)); off += 8; }
const mask    = masked ? data.slice(off, off + 4) : null;
if (masked) off += 4;
if (off + plen > data.length) break;
let payload = data.slice(off, off + plen);
if (masked) {
payload = Buffer.from(payload);
for (let i = 0; i < payload.length; i++) payload[i] ^= mask[i % 4];
}
off += plen;
frames.push({ opcode, payload, fin });
}
return frames;
}

// ── HTTP server ───────────────────────────────────────────────────────────
const clients = new Map();  // socket → { pingTimer, addr }

const server = http.createServer((req, res) => {
if (req.url === ‘/health’ || req.url === ‘/’) {
res.writeHead(200, { ‘Content-Type’: ‘application/json’ });
res.end(JSON.stringify({
status:       ‘ok’,
service:      ‘node-bridge’,
bridge_port:  BRIDGE_PORT,
backend_url:  BACKEND_URL,
keycloak_url: KC_URL,
clients:      clients.size,
uptime_s:     Math.floor(process.uptime()),
ports: { bridge: BRIDGE_PORT, python: 9897, koder: 9898, kc: ‘8080/8443’, pg: 5432, redis: 6379 },
}));
return;
}
res.writeHead(404);
res.end(‘Not found’);
});

// ── WebSocket upgrade handler ─────────────────────────────────────────────
server.on(‘upgrade’, (req, socket) => {
const key = req.headers[‘sec-websocket-key’];
if (!key || req.headers[‘upgrade’]?.toLowerCase() !== ‘websocket’) {
socket.destroy();
return;
}

const accept = wsAccept(key);
socket.write(
‘HTTP/1.1 101 Switching Protocols\r\n’ +
‘Upgrade: websocket\r\n’ +
‘Connection: Upgrade\r\n’ +
`Sec-WebSocket-Accept: ${accept}\r\n` +
‘Access-Control-Allow-Origin: *\r\n’ +
‘\r\n’
);

const addr = `${req.socket.remoteAddress}:${req.socket.remotePort}`;
log.info(`Client connected — ${addr} path=${req.url} total=${clients.size + 1}`);

// Immediate handshake
wsSend(socket, {
type:        ‘bridge_handshake’,
status:      ‘connected’,
bridge_port: BRIDGE_PORT,
backend_url: BACKEND_URL,
ports: { bridge: BRIDGE_PORT, python: 9897, koder: 9898, kc: ‘8080/8443’, pg: 5432, redis: 6379 },
ts:          Date.now(),
});

// Heartbeat ping
const pingTimer = setInterval(() => {
if (!socket.destroyed) {
socket.write(Buffer.from([0x89, 0x00])); // WS ping frame
}
}, PING_MS);

clients.set(socket, { pingTimer, addr });

let buf = Buffer.alloc(0);

socket.on(‘data’, async (chunk) => {
buf = Buffer.concat([buf, chunk]);
const frames = wsRead(buf);
buf = Buffer.alloc(0); // frames fully consumed

```
for (const frame of frames) {
  if (frame.opcode === 0x8) {  // Close
    socket.destroy();
    return;
  }
  if (frame.opcode === 0x9) {  // Ping
    socket.write(Buffer.from([0x8A, 0x00]));
    continue;
  }
  if (frame.opcode === 0xA) continue;  // Pong

  if (frame.opcode === 0x1 || frame.opcode === 0x2) {
    let msg;
    try { msg = JSON.parse(frame.payload.toString('utf8')); }
    catch {
      wsSend(socket, { type: 'error', message: 'Invalid JSON', ts: Date.now() });
      continue;
    }

    log.debug(`→ python [${msg.type}]`);

    try {
      const result = await dispatchToPython(msg);
      if (!socket.destroyed) wsSend(socket, result);
    } catch(err) {
      log.error(`Python dispatch failed [${msg.type}]: ${err.message}`);
      if (!socket.destroyed) {
        wsSend(socket, {
          type:          'error',
          message:       'Python backend unreachable',
          backend_url:   BACKEND_URL,
          detail:        err.message,
          original_type: msg.type,
          hint:          `Start: python3 bridge.py (port 9897)`,
          ts:            Date.now(),
        });
      }
    }
  }
}
```

});

socket.on(‘close’, () => {
const meta = clients.get(socket);
if (meta) {
clearInterval(meta.pingTimer);
clients.delete(socket);
}
log.info(`Client disconnected — ${addr} total=${clients.size}`);
});

socket.on(‘error’, (err) => {
const meta = clients.get(socket);
if (meta) { clearInterval(meta.pingTimer); clients.delete(socket); }
log.error(`Socket error — ${addr}: ${err.message}`);
});
});

// ── Start ─────────────────────────────────────────────────────────────────
server.listen(BRIDGE_PORT, BRIDGE_HOST, () => {
log.info(`Node WS bridge  →  ws://${BRIDGE_HOST}:${BRIDGE_PORT}`);
log.info(`Python upstream →  ${BACKEND_URL}`);
log.info(`Keycloak auth   →  ${KC_URL}`);
console.log(’\nPort map:’);
console.log(`  ${BRIDGE_PORT}       ← this bridge (WS)`);
console.log(`  9897       ← Python bridge`);
console.log(`  9898       ← KODER app`);
console.log(`  8080/8443  ← Keycloak`);
console.log(`  5432       ← PostgreSQL`);
console.log(`  6379       ← Redis\n`);
});

// ── Graceful shutdown ─────────────────────────────────────────────────────
function shutdown(sig) {
log.info(`${sig} — closing ${clients.size} connections`);
clients.forEach((meta, socket) => {
clearInterval(meta.pingTimer);
try {
wsSend(socket, { type: ‘bridge_shutdown’, ts: Date.now() });
socket.destroy();
} catch(_e) {}
});
server.close(() => {
log.info(‘Bridge shut down cleanly’);
process.exit(0);
});
setTimeout(() => process.exit(1), 5000);
}
process.on(‘SIGTERM’, () => shutdown(‘SIGTERM’));
process.on(‘SIGINT’,  () => shutdown(‘SIGINT’));
process.on(‘uncaughtException’, (e) => log.error(‘Uncaught:’, e.message));
