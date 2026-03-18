# FullDashboard Setup Guide

## Overview

The FullDashboard.html is now fully integrated with the Unified Server on port 9898. This comprehensive dashboard provides a complete interface for all SuperGrok Heavy 4.2 features.

## Quick Start

### 1. Start the Unified Server

```bash
# Navigate to the project root
cd /path/to/SuperGrok-Heavy-4-2-Skeleton

# Start the server (port 9898)
node Unified_Server.js

# OR use npm
npm start

# OR with verbose logging
npm run dev
```

### 2. Access the Dashboard

Open your browser and navigate to:

- **Main Dashboard**: http://127.0.0.1:9898/
- **Alternative URLs**:
  - http://127.0.0.1:9898/dashboard
  - http://127.0.0.1:9898/FullDashboard.html

## Architecture

### Unified Port 9898

All services are consolidated through port 9898:

```
┌─────────────────────────────────────────┐
│         FullDashboard.html              │
│  (Browser - served from port 9898)      │
└──────────────┬──────────────────────────┘
               │
               │ HTTP: http://127.0.0.1:9898
               │ WebSocket: ws://127.0.0.1:9898
               │
               ▼
┌─────────────────────────────────────────┐
│       Unified_Server.js                 │
│       (Node.js - Port 9898)             │
│                                         │
│  • HTTP Server (static files + API)    │
│  • WebSocket Server (real-time)        │
│  • Authentication & Authorization       │
│  • TTS (Piper + Coqui)                 │
│  • AI Proxy (Claude, GPT, Grok)        │
│  • DDG Search                           │
│  • GitHub OAuth                         │
│  • Plaid Integration                    │
│  • Memory Store                         │
│  • Audit Logging                        │
└─────────────────────────────────────────┘
```

## Dashboard Features

The FullDashboard provides access to:

### Core Features
- **Role-Based Authentication**: Multi-level access control with passphrase protection
- **AI Chat**: Claude, GPT-4o, Grok integration
- **WebSocket Bridge**: Real-time communication on port 9898
- **TTS Services**: Piper and Coqui text-to-speech
- **DDG Search**: Privacy-focused search integration

### Role Management
- **165+ Role Types**: From Root/Superadmin to specialized roles
- **Level-Based Access**: 0-6 security clearance levels
- **Child Protection**: Automatic blocking of high-security roles for children
- **Panel Access Control**: Role-specific dashboard panels

### Advanced Features
- **Bridge Configuration**: Customizable connection settings
- **Keycloak Integration**: SSO and identity management
- **Memory System**: Persistent session storage
- **Audit Trail**: Comprehensive logging with HMAC chain
- **Diagnostic Tools**: Real-time server health monitoring
- **Code Tools**: Syntax checking and auto-fix

## Connection Configuration

The dashboard automatically connects to port 9898. Connection settings in the HTML:

```javascript
// WebSocket Connection (line 1830)
var wsUrl = 'ws://127.0.0.1:9898'; /* 9898 ONLY */

// HTTP Fallback (lines 1897-1898)
fetch('http://127.0.0.1:9898/health')  // Bridge health + direct
fetch('http://127.0.0.1:9898/health')  // Direct fallback
```

## Server Endpoints

### HTTP Endpoints

**Health Check**
- `GET /health` - Server health status
- `GET /api/health` - API health status

**Dashboard**
- `GET /` - Serve FullDashboard.html
- `GET /dashboard` - Serve FullDashboard.html
- `GET /FullDashboard.html` - Serve FullDashboard.html

**Authentication**
- `POST /api/auth/login` - User login
- `POST /api/auth/verify-panel` - Verify panel access
- `POST /api/auth/verify-passphrase` - Verify passphrase
- `POST /api/auth/refresh` - Refresh auth token
- `POST /api/auth/webauthn/challenge` - WebAuthn challenge
- `GET /api/auth/child-block` - Check if role is child-blocked

**Logging**
- `POST /api/logs/event` - Log client event
- `GET /api/logs/access` - Get access logs (admin only)

**Commands**
- `POST /api/execute-command` - Execute shell command

### WebSocket Messages

**Connection**
- `ping` → `pong` - Health check with server status
- `diagnostic` → `diagnostic_report` - Full server diagnostics

**TTS**
- `piper_speak` / `speak` → `audio` - Piper TTS
- `coqui_speak` → `audio` - Coqui TTS
- `tts_speak` → `audio` - Auto-select TTS engine
- `tts_status` → Status of TTS services

**AI & Search**
- `ai_query` → `ai_response` - AI model query
- `ddg_search` → `ddg_result` - DuckDuckGo search

**Authentication**
- `token_verify` → `token_ok` / `token_invalid` - Verify JWT
- `mfa_gen` → `mfa_token` - Generate MFA token
- `mfa_verify` → `mfa_result` - Verify MFA token

**Data**
- `memory_save` → `memory_saved` - Save memory card
- `memory_get` → `memory_result` - Retrieve memory cards
- `collab_broadcast` → `collab_ack` - Broadcast to all clients

**Integrations**
- `gh_exchange` → `gh_token` - GitHub OAuth
- `plaid_link_token` → Plaid integration
- `plaid_exchange` → Exchange Plaid token
- `plaid_balance` → Get account balance

**Development**
- `shell_cmd` → `shell_output` - Execute shell command
- `code_check` → `code_check_result` - Syntax check
- `code_fix` → `code_fix_result` - Auto-fix code
- `dashboard_build` → `dashboard_built` - Build custom dashboard
- `audit_export` → `audit_data` - Export audit logs

**Advanced**
- `movie_generate` → `movie_job` - Movie generation job
- `music_generate` → `music_job` - Music generation job
- `opar_interact` → `opar_response` - OP-AR interaction
- `opar_design` → `opar_design_ack` - OP-AR design update
- `cgi_avatar_update` → `cgi_avatar_ack` - Avatar update

## Environment Configuration

Create a `.env` file (copy from `.env.example`):

```bash
# Server - UNIFIED PORT ARCHITECTURE
PORT_UNIFIED=9898
PORT_BRIDGE=9898
PORT_AUTH=9898

# Logging
LOG_DIR=./logs
VERBOSE=0

# TTS (optional)
COQUI_URL=http://localhost:5002

# AI API Keys (optional - set at least one)
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...
XAI_API_KEY=xai-...

# GitHub OAuth (optional)
GH_CLIENT_ID=...
GH_CLIENT_SECRET=...

# Shell Commands (optional - default disabled)
ALLOW_SHELL=0
```

## Security Features

### Master Key
- Auto-generated 64-byte key on first run
- Stored in `.sg_master_key` (in .gitignore)
- Used for JWT signing and HMAC audit chains

### Audit Trail
- All events logged to `logs/access.jsonl`
- HMAC-SHA256 hash chaining for tamper detection
- ISO 8601 timestamps in UTC

### Rate Limiting
- 60 requests per minute per IP (HTTP)
- 80 messages per minute per WebSocket
- Automatic fail-lock after 5 failed auth attempts

### Role-Based Access
- 165+ predefined roles with specific clearance levels
- Panel-level access control
- Passphrase protection for high-security roles
- Child-block for sensitive roles

## Troubleshooting

### Dashboard Won't Load

1. Check if server is running:
```bash
curl http://127.0.0.1:9898/health
```

2. Verify FullDashboard.html exists in project root:
```bash
ls -la FullDashboard.html
```

3. Check server logs:
```bash
tail -f logs/access.jsonl
```

### WebSocket Connection Fails

1. Verify port 9898 is not blocked:
```bash
lsof -i :9898
```

2. Check browser console for CSP errors
3. Ensure using `ws://` not `wss://` for localhost

### TTS Not Working

1. Check TTS status via diagnostic:
   - Open dashboard
   - WebSocket should show TTS availability

2. For Piper TTS:
   - Download Piper binary and model
   - Set `PIPER_BIN` and `PIPER_MODEL` in .env

3. For Coqui TTS:
   - Start Coqui server: `python coqui_tts_service.py --serve`
   - Verify `COQUI_URL` in .env

### AI Features Not Working

Set at least one API key in `.env`:
```bash
ANTHROPIC_API_KEY=sk-ant-...
# OR
OPENAI_API_KEY=sk-...
# OR
XAI_API_KEY=xai-...
```

## Development

### Running with Verbose Logging

```bash
VERBOSE=1 node Unified_Server.js
# OR
npm run dev
```

### Enabling Shell Commands

```bash
ALLOW_SHELL=1 node Unified_Server.js
# OR
npm run shell
```

### Testing the Server

```bash
# Syntax check
npm run check

# Test health endpoint
curl http://127.0.0.1:9898/health

# Test WebSocket (using websocat)
websocat ws://127.0.0.1:9898
{"type":"ping"}
```

## File Locations

- **Server**: `Unified_Server.js`
- **Dashboard**: `FullDashboard.html`
- **Config**: `.env` (create from `.env.example`)
- **Master Key**: `.sg_master_key` (auto-generated)
- **Logs**: `logs/access.jsonl`

## Integration Checklist

- [x] FullDashboard.html connects to ws://127.0.0.1:9898
- [x] Unified_Server.js serves FullDashboard.html on port 9898
- [x] All HTTP APIs accessible through port 9898
- [x] WebSocket bridge operational on port 9898
- [x] Authentication system integrated
- [x] TTS services (Piper + Coqui) available
- [x] AI proxy (Claude, GPT, Grok) configured
- [x] Memory store and audit logging active
- [x] Rate limiting and security features enabled
- [x] Documentation complete

## Next Steps

1. **Start the Server**:
   ```bash
   npm start
   ```

2. **Open Dashboard**:
   http://127.0.0.1:9898/

3. **Select Your Role**:
   - Browse available roles
   - Enter credentials
   - Access role-specific panels

4. **Explore Features**:
   - Try AI chat
   - Test TTS
   - Configure bridge settings
   - Review audit logs

## Support

For issues or questions:
- Check server logs in `logs/access.jsonl`
- Review audit trail for errors
- Verify environment configuration
- Test endpoints manually with curl

---

**Last Updated**: March 12, 2026
**Dashboard Version**: FullDashboard.html (23,686 lines)
**Server Version**: Unified_Server.js v13.1.0
**Port Architecture**: Unified 9898
