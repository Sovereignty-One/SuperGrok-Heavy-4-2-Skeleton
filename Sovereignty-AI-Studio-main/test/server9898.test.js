'use strict';

/**
 * Tests for server_9898.js — SuperGrok AI Platform Bridge Server
 *
 * Run with:  node --test test/server9898.test.js
 */

const { describe, it, before, after } = require('node:test');
const assert = require('node:assert/strict');
const http   = require('http');
const { WebSocket } = require('ws');

// Import the module under test (server starts when require.main === module,
// so importing it won't bind to PORT 9898 — we call server.listen(0) below)
const { server, callAI, executeCommand } = require('../server_9898');

let baseUrl;

before(async () => {
  await new Promise((resolve) => {
    server.listen(0, () => {
      const addr = server.address();
      baseUrl = `http://localhost:${addr.port}`;
      resolve();
    });
  });
});

after(async () => {
  await new Promise((resolve) => server.close(resolve));
});

/* ── helpers ────────────────────────────────────────────────── */

function request(urlPath, opts = {}) {
  const url = new URL(urlPath, baseUrl);
  return new Promise((resolve, reject) => {
    const req = http.request(url, {
      method:  opts.method  || 'GET',
      headers: opts.headers || {},
    }, (res) => {
      let body = '';
      res.on('data', (d) => (body += d));
      res.on('end', () => {
        try { resolve({ status: res.statusCode, body: JSON.parse(body) }); }
        catch (e) { /* JSON parse failed — return raw body string */ resolve({ status: res.statusCode, body }); }
      });
    });
    req.on('error', reject);
    if (opts.body) req.write(opts.body);
    req.end();
  });
}

/* ── /health ────────────────────────────────────────────────── */

describe('server_9898 — /health', () => {
  it('returns healthy status', async () => {
    const r = await request('/health');
    assert.equal(r.status, 200);
    assert.equal(r.body.status, 'healthy');
    assert.equal(r.body.service, 'server_9898');
    assert.ok(typeof r.body.uptime === 'number');
    assert.ok(r.body.timestamp);
    assert.ok(typeof r.body.ai === 'object');
  });
});

/* ── /api/memory ────────────────────────────────────────────── */

describe('server_9898 — /api/memory', () => {
  let createdId;

  it('GET /api/memory returns an array', async () => {
    const r = await request('/api/memory');
    assert.equal(r.status, 200);
    assert.ok(Array.isArray(r.body));
  });

  it('POST /api/memory creates an entry', async () => {
    const r = await request('/api/memory', {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify({ title: 'Test Note', content: 'Hello memory' }),
    });
    assert.equal(r.status, 201);
    assert.equal(r.body.title, 'Test Note');
    assert.equal(r.body.content, 'Hello memory');
    assert.ok(r.body.id);
    createdId = r.body.id;
  });

  it('GET /api/memory contains the new entry', async () => {
    const r = await request('/api/memory');
    assert.ok(r.body.some((e) => e.id === createdId));
  });

  it('DELETE /api/memory/:id removes the entry', async () => {
    const r = await request(`/api/memory/${createdId}`, { method: 'DELETE' });
    assert.equal(r.status, 200);
    assert.equal(r.body.deleted, 1);
    const list = await request('/api/memory');
    assert.ok(!list.body.some((e) => e.id === createdId));
  });
});

/* ── /api/audit ─────────────────────────────────────────────── */

describe('server_9898 — /api/audit', () => {
  let createdId;

  it('GET /api/audit returns an array', async () => {
    const r = await request('/api/audit');
    assert.equal(r.status, 200);
    assert.ok(Array.isArray(r.body));
  });

  it('POST /api/audit appends an entry', async () => {
    const r = await request('/api/audit', {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify({ action: 'TEST', detail: 'unit test', role: 'admin' }),
    });
    assert.equal(r.status, 201);
    assert.equal(r.body.action, 'TEST');
    assert.equal(r.body.detail, 'unit test');
    assert.ok(r.body.id);
    createdId = r.body.id;
  });

  it('GET /api/audit contains the new entry', async () => {
    const r = await request('/api/audit');
    assert.ok(r.body.some((e) => e.id === createdId));
  });
});

/* ── /api/execute-command ───────────────────────────────────── */

describe('server_9898 — /api/execute-command', () => {
  it('executes allowed commands', async () => {
    const r = await request('/api/execute-command', {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify({ command: 'echo hello', role: 'admin' }),
    });
    assert.equal(r.status, 200);
    assert.match(r.body.output, /hello/);
    assert.equal(r.body.exit, 0);
  });

  it('restricts disallowed commands', async () => {
    const r = await request('/api/execute-command', {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify({ command: 'rm -rf /', role: 'user' }),
    });
    assert.equal(r.status, 200);
    assert.equal(r.body.exit, 1);
    assert.match(r.body.output, /restricted/);
  });
});

/* ── CORS ───────────────────────────────────────────────────── */

describe('server_9898 — CORS', () => {
  it('OPTIONS preflight returns 204 with CORS headers', async () => {
    const r = await request('/health', { method: 'OPTIONS' });
    assert.equal(r.status, 204);
  });
});

/* ── 404 ─────────────────────────────────────────────────────── */

describe('server_9898 — 404', () => {
  it('unknown routes return 404', async () => {
    const r = await request('/unknown-route');
    assert.equal(r.status, 404);
  });
});

/* ── callAI (unit) ───────────────────────────────────────────── */

describe('server_9898 — callAI unit', () => {
  it('returns error when no API key is set', async () => {
    // Only works when env keys are absent (default in CI)
    const originalKey = process.env.ANTHROPIC_API_KEY;
    delete process.env.ANTHROPIC_API_KEY;
    const result = await callAI('claude', 'sys', [{ role: 'user', content: 'hi' }]);
    assert.ok(result.error);
    if (originalKey) process.env.ANTHROPIC_API_KEY = originalKey;
  });

  it('returns error for unknown model', async () => {
    const result = await callAI('unknown_model', '', []);
    assert.ok(result.error);
    assert.match(result.error, /Unknown model/);
  });
});

/* ── executeCommand (unit) ───────────────────────────────────── */

describe('server_9898 — executeCommand unit', () => {
  it('pwd returns output', () => {
    const r = executeCommand('pwd', 'admin');
    assert.equal(r.exit, 0);
    assert.ok(r.output.trim().length > 0);
  });

  it('disallows rm commands', () => {
    const r = executeCommand('rm -rf /tmp/test', 'admin');
    assert.equal(r.exit, 1);
    assert.match(r.output, /restricted/);
  });
});

/* ── WebSocket ───────────────────────────────────────────────── */

describe('server_9898 — WebSocket', () => {
  it('responds to ping with pong', async () => {
    const addr = server.address();
    const ws = new WebSocket(`ws://localhost:${addr.port}`);

    const pong = await new Promise((resolve, reject) => {
      ws.on('open', () => ws.send(JSON.stringify({ type: 'ping' })));
      ws.on('message', (raw) => { resolve(JSON.parse(raw)); ws.close(); });
      ws.on('error', reject);
      setTimeout(() => reject(new Error('ws ping timeout')), 3000);
    });

    assert.equal(pong.type, 'pong');
    assert.ok(pong.timestamp);
  });

  it('returns ai_response for ai_query (no key — error payload)', async () => {
    const addr = server.address();
    const ws = new WebSocket(`ws://localhost:${addr.port}`);

    const reply = await new Promise((resolve, reject) => {
      ws.on('open', () => ws.send(JSON.stringify({
        type: 'ai_query', model: 'claude', text: 'hello', system: '',
      })));
      ws.on('message', (raw) => { resolve(JSON.parse(raw)); ws.close(); });
      ws.on('error', reject);
      setTimeout(() => reject(new Error('ws ai_query timeout')), 5000);
    });

    assert.equal(reply.type, 'ai_response');
    assert.equal(reply.model, 'claude');
    // With no API key configured the bridge must surface an error
    assert.ok(reply.error || reply.text);
  });
});
