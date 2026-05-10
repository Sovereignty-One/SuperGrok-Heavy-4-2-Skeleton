'use strict';
/**
 * websocket.js — External WebSocket / Telemetry Server (Port 9899)
 *
 * Accepts inbound WebSocket connections, logs telemetry messages, and
 * broadcasts a heartbeat to every connected client once per second.
 *
 * This server sits behind the Caddy reverse proxy at /ws/* and is
 * isolated from the main Node.js Unified_Server.js relay.
 *
 * Run:
 *   node websocket.js
 *
 * Environment variables:
 *   WS_PORT   — listen port (default: 9899)
 */

const { WebSocket, WebSocketServer } = require('ws');

const PORT = parseInt(process.env.WS_PORT || '9899', 10);
const wss  = new WebSocketServer({ port: PORT });

console.log(`WebSocket telemetry server running on ${PORT}`);

wss.on('connection', ws => {
  console.log(`[ws] client connected  (total: ${wss.clients.size})`);

  // Send one heartbeat per second while the socket is open.
  const heartbeatTimer = setInterval(() => {
    if (ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({ heartbeat: Date.now() }));
    }
  }, 1000);

  ws.on('message', raw => {
    try {
      const msg = JSON.parse(raw);
      console.log('[ws] received telemetry:', msg);
    } catch {
      console.warn('[ws] non-JSON message received');
    }
  });

  ws.on('close', () => {
    clearInterval(heartbeatTimer);
    console.log(`[ws] client disconnected (total: ${wss.clients.size})`);
  });

  ws.on('error', err => {
    clearInterval(heartbeatTimer);
    console.error('[ws] socket error:', err.message);
  });
});

wss.on('error', err => {
  console.error('[ws] server error:', err.message);
  process.exit(1);
});
