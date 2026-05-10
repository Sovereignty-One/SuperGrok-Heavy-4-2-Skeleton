/**
 * SuperGrok v82 -- Bridge Git Handler
 *
 * Call handleBridgeMessage(msg, ws) from inside your WebSocket message handler
 * in Unified_Server.js (where existing cases like 'ai_query', 'ping', etc.
 * are handled).
 *
 * Handles: git_push, git_status, key_rotate, memory_sync, agent_status_request
 *
 * Usage in Unified_Server.js:
 *   const { handleBridgeMessage } = require('./Bridge_Githandler');
 *   // inside ws.on('message', async (raw) => { ... })
 *   if (handleBridgeMessage(msg, ws)) return;
 */

'use strict';

const { exec } = require('child_process');
const fs   = require('fs');
const path = require('path');

/**
 * Handle a WebSocket message for git/key/memory/agent operations.
 * Returns true if the message was handled, false otherwise.
 *
 * @param {{ type: string, [key: string]: any }} msg - parsed message object
 * @param {import('ws').WebSocket} ws - the WebSocket connection
 * @returns {boolean}
 */
function handleBridgeMessage(msg, ws) {
  switch (msg.type) {

    case 'git_push': {
      const remote  = (msg.remote  || '').replace(/[^a-zA-Z0-9@:./*-]/g, '');
      const branch  = (msg.branch  || 'main').replace(/[^a-zA-Z0-9/*-]/g, '');
      const message = (msg.message || 'chore: SuperGrok update').replace(/["`$\\]/g, ' ');

      if (!remote) {
        ws.send(JSON.stringify({ type: 'git_push_result', success: false, message: 'No remote' }));
        return true;
      }

      const cmd = `git add -A && git commit -m "${message}" --allow-empty && git push "${remote}" ${branch}`;
      exec(cmd, { timeout: 30000 }, (err, stdout, stderr) => {
        ws.send(JSON.stringify({
          type:    'git_push_result',
          success: !err,
          repo:    msg.repo || remote,
          output:  (stdout || '') + (stderr || '') + (err ? '\nERR: ' + err.message : ''),
          message: err ? err.message : 'Pushed successfully',
        }));
      });
      return true;
    }

    case 'git_status': {
      exec(
        'git status --short && echo "---" && git log --oneline -5 && echo "---" && git remote -v',
        { timeout: 5000 },
        (err, stdout, stderr) => {
          ws.send(JSON.stringify({
            type:    'git_status_result',
            output:  stdout || stderr || 'No output',
            success: !err,
          }));
        },
      );
      return true;
    }

    case 'key_rotate': {
      // Rotate to next available API key from pool
      const keys = {
        anthropic: (process.env.ANTHROPIC_API_KEY_POOL || process.env.ANTHROPIC_API_KEY || '').split(',').filter(Boolean),
        openai:    (process.env.OPENAI_API_KEY_POOL    || process.env.OPENAI_API_KEY    || '').split(',').filter(Boolean),
        xai:       (process.env.XAI_API_KEY_POOL       || process.env.XAI_API_KEY       || '').split(',').filter(Boolean),
      };

      let rotated = false;
      Object.keys(keys).forEach(provider => {
        if (keys[provider].length > 1) {
          // Rotate: move head to tail
          const k = keys[provider].shift();
          keys[provider].push(k);
          // Update active key in process.env
          if (provider === 'anthropic') process.env.ANTHROPIC_API_KEY = keys[provider][0];
          if (provider === 'openai')    process.env.OPENAI_API_KEY    = keys[provider][0];
          if (provider === 'xai')       process.env.XAI_API_KEY       = keys[provider][0];
          rotated = true;
        }
      });

      ws.send(JSON.stringify({ type: 'key_rotated', rotated, reason: msg.reason || 'manual', ts: Date.now() }));
      return true;
    }

    case 'memory_sync': {
      // Store memory cards server-side (append to session log)
      const logDir = process.env.LOG_DIR || './logs';
      if (!fs.existsSync(logDir)) fs.mkdirSync(logDir, { recursive: true });
      const memLog = path.join(logDir, 'memory_sync.jsonl');
      const cards  = Array.isArray(msg.cards) ? msg.cards.slice(0, 50) : [];

      cards.forEach(c => {
        try {
          fs.appendFileSync(memLog, JSON.stringify({ ...c, bridge_ts: Date.now() }) + '\n');
        } catch (_) { /* ignore individual write errors */ }
      });

      ws.send(JSON.stringify({ type: 'memory_saved', count: cards.length, ts: Date.now() }));
      return true;
    }

    case 'agent_status_request': {
      // Report which agent backends are configured
      const statuses = {
        claude:  !!process.env.ANTHROPIC_API_KEY      ? 'online' : 'offline',
        gpt:     !!process.env.OPENAI_API_KEY         ? 'online' : 'offline',
        grok:    !!process.env.XAI_API_KEY            ? 'online' : 'offline',
        copilot: !!process.env.GITHUB_COPILOT_TOKEN   ? 'online' : 'offline',
        watcher: 'online',
      };

      Object.keys(statuses).forEach(agent => {
        ws.send(JSON.stringify({ type: 'agent_status', agent, status: statuses[agent] }));
      });
      return true;
    }

    default:
      return false;
  }
}

module.exports = { handleBridgeMessage };
