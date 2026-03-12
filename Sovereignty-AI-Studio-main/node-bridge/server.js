/**
 * Sovereignty AI Studio — Node.js Communication Bridge
 *
 * Connects the React frontend, Python backends (FastAPI + Quart), and
 * iSH / Code Pad developer environments through a single entry-point.
 *
 * Endpoints:
 *   GET  /health                  – bridge health check
 *   ALL  /api/v1/*                – proxy to FastAPI  (BACKEND_URL)
 *   ALL  /api/weather*            – proxy to Quart    (WEATHER_URL)
 *   ALL  /api/forecast*           – proxy to Quart    (WEATHER_URL)
 *   POST /api/bridge/notify       – push real-time alert to WebSocket clients
 *   WS   /ws/alerts               – WebSocket for live alerts
 */

const express = require('express');
const http = require('http');
const { WebSocketServer } = require('ws');

// ---------------------------------------------------------------------------
// Config from environment (sensible defaults for local / iSH)
// ---------------------------------------------------------------------------
const BACKEND_URL = process.env.BACKEND_URL || 'http://127.0.0.1:9898';
const WEATHER_URL = process.env.WEATHER_URL || 'http://127.0.0.1:9898';
const PORT = parseInt(process.env.NODE_BRIDGE_PORT || '9898', 10);

const app = express();
app.use(express.json());

// ---------------------------------------------------------------------------
// CORS — default to 127.0.0.1:9898
// ---------------------------------------------------------------------------
app.use((_req, res, next) => {
  const origin = process.env.CORS_ORIGIN || 'http://127.0.0.1:9898';
  res.setHeader('Access-Control-Allow-Origin', origin);
  res.setHeader('Access-Control-Allow-Methods', 'GET,POST,PATCH,DELETE,OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type,Authorization');
  if (_req.method === 'OPTIONS') return res.sendStatus(204);
  next();
});

// ---------------------------------------------------------------------------
// Health check
// ---------------------------------------------------------------------------
app.get('/health', (_req, res) => {
  res.json({
    status: 'healthy',
    service: 'node-bridge',
    uptime: process.uptime(),
    backends: { api: BACKEND_URL, weather: WEATHER_URL },
    timestamp: new Date().toISOString(),
  });
});

// ---------------------------------------------------------------------------
// Lightweight reverse proxy (no extra dependency)
// ---------------------------------------------------------------------------
function proxyRequest(targetBase, req, res) {
  const url = new URL(req.originalUrl, targetBase);
  const options = {
    hostname: url.hostname,
    port: url.port,
    path: url.pathname + url.search,
    method: req.method,
    headers: { ...req.headers, host: url.host },
  };

  const proxyReq = http.request(options, (proxyRes) => {
    res.writeHead(proxyRes.statusCode, proxyRes.headers);
    proxyRes.pipe(res, { end: true });
  });

  proxyReq.on('error', (err) => {
    console.error(`[proxy] ${targetBase} error:`, err.message);
    if (!res.headersSent) {
      res.status(502).json({ error: 'Backend unavailable', target: targetBase });
    }
  });

  req.pipe(proxyReq, { end: true });
}

// Proxy /api/v1/* → FastAPI
app.use('/api/v1', (req, res) => proxyRequest(BACKEND_URL, req, res));

// Proxy /api/weather* and /api/forecast* → Quart
app.use('/api/weather', (req, res) => proxyRequest(WEATHER_URL, req, res));
app.use('/api/forecast', (req, res) => proxyRequest(WEATHER_URL, req, res));

// ---------------------------------------------------------------------------
// WebSocket — real-time alert channel
// ---------------------------------------------------------------------------
const server = http.createServer(app);
const wss = new WebSocketServer({ server, path: '/ws/alerts' });
const clients = new Set();

wss.on('connection', (ws) => {
  clients.add(ws);
  console.log(`[ws] client connected (${clients.size} total)`);

  ws.on('close', () => {
    clients.delete(ws);
    console.log(`[ws] client disconnected (${clients.size} total)`);
  });

  ws.on('message', (raw) => {
    try {
      const msg = JSON.parse(raw);
      if (msg.type === 'ping') {
        ws.send(JSON.stringify({ type: 'pong', timestamp: new Date().toISOString() }));
      }
    } catch {
      // ignore malformed messages
    }
  });
});

function broadcast(data) {
  const payload = JSON.stringify(data);
  for (const ws of clients) {
    if (ws.readyState === 1) ws.send(payload);  // 1 === WebSocket.OPEN
  }
}

// POST /api/bridge/notify — Python backends can push alerts here
app.post('/api/bridge/notify', (req, res) => {
  const { type, title, message, severity } = req.body;
  if (!type || !title) {
    return res.status(400).json({ error: 'type and title are required' });
  }
  const alert = {
    type,
    title,
    message: message || '',
    severity: severity || 'info',
    timestamp: new Date().toISOString(),
  };
  broadcast(alert);
  res.json({ sent: clients.size, alert });
});

// ---------------------------------------------------------------------------
// Start (only when run directly, not when imported for tests)
// ---------------------------------------------------------------------------
if (require.main === module) {
  server.listen(PORT, '127.0.0.1', () => {
    console.log(`[node-bridge] listening on http://127.0.0.1:${PORT}`);
    console.log(`[node-bridge] WebSocket   ws://127.0.0.1:${PORT}/ws/alerts`);
    console.log(`[node-bridge] proxy /api/v1/*      → ${BACKEND_URL}`);
    console.log(`[node-bridge] proxy /api/weather/*  → ${WEATHER_URL}`);
    console.log(`[node-bridge] proxy /api/forecast/* → ${WEATHER_URL}`);
  });
}

module.exports = { app, server, wss, broadcast };
