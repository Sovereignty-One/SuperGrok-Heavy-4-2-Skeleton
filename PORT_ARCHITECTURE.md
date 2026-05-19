# Port Architecture

## Overview

The SuperGrok Heavy 4.2 Skeleton uses a clear three-port separation:

| Port | Service | Role |
|------|---------|------|
| **9897** | `python3_bridge.py` | Python Bridge — backend AI, brain/memory, key rotation, audit |
| **9898** | `server_9898.js` (repo root) | KODER frontend / Dashboard — HTML, WebSocket, Coder UI, everything the user sees |
| **9899** | `Unified_Server.js` | Node.js external backend — REST proxy / relay |
| **8080** | Keycloak | SSO / Identity Provider (HTTP) |
| **8443** | Keycloak | SSO / Identity Provider (HTTPS) |

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                  External Clients                            │
│  • iOS App / iSH / macOS (ws://127.0.0.1:9897)             │
│  • KODER / SGHv119 frontend (http://127.0.0.1:9898)        │
│  • Node external backend    (http://127.0.0.1:9899)        │
│  • Keycloak admin          (http://localhost:8080/admin/)   │
└──────┬──────────────────────────┬──────────────┬────────────┘
       │ Port 9897                │ Port 9898    │ Port 9899
       ▼                          ▼              ▼
┌──────────────────┐  ┌─────────────────────┐  ┌──────────────────┐
│ python3_bridge.py│  │  server_9898.js     │  │ Unified_Server.js│
│ Python Bridge    │  │  KODER frontend     │  │ Node external    │
│ • AI / brain     │  │  Dashboard          │  │ • REST proxy     │
│ • Key rotation   │  │  • Serves HTML      │  │ • WS relay       │
│ • Audit log      │  │  • WebSocket bus    │  │ • /api/v1/*      │
│ • /api/brain     │  │  • Coder / editor   │  └──────────────────┘
└──────────────────┘  └─────────────────────┘
```

## Port Assignment

### 9897 — Python Bridge (`python3_bridge.py`)
- Backend AI: Claude / OpenAI / Grok with newest-first model-chain fallback
- Persistent brain: `memory_save/get/delete/clear` WS + `GET|POST /api/brain` HTTP
- Key rotation, audit log (`~/.sg_audit.jsonl`), session tokens
- API routes: `/api/health`, `/api/ai`, `/api/keys`, `/api/speak`, `/api/audit`, `/api/rotate-key`, `/api/conflicts`, `/api/brain`

### 9898 — KODER Frontend / Dashboard (`server_9898.js`, repo root)
- Serves `SGHv119.html` and all dashboard HTML to the browser
- WebSocket channel for real-time UI updates
- AI proxy pass-through, memory, audit endpoints
- **This is what the user sees — browser connects here**

### 9899 — Node.js Unified Server (`Unified_Server.js`)
- External backend / REST API proxy
- WebSocket relay
- Docker bridge service

### 8080 / 8443 — Keycloak
- Admin console at `http://localhost:8080/admin/`
- Configure `KC_HTTPS_CERTIFICATE_FILE` / `KC_HTTPS_CERTIFICATE_KEY_FILE` for HTTPS

### Internal Ports (Docker Network Only)
- **6379**: Redis (127.0.0.1, protected mode)
- **5432**: PostgreSQL (internal Docker network)

## Quick Start

### Standalone (iSH / macOS / Linux — no Docker)
```bash
# Set API keys
export ANTHROPIC_API_KEY=sk-ant-...
export OPENAI_API_KEY=sk-...
export GROK_API_KEY=xai-...

# Start Python bridge (backend)
python3 python3_bridge.py
# → http://127.0.0.1:9897

# Start KODER Frontend / Dashboard (in another terminal)
node server_9898.js
# → http://127.0.0.1:9898  ← open this in your browser

# Or start everything at once
./Start_All.sh
```

### Docker Compose
```bash
cd Sovereignty-AI-Studio-main
docker-compose up -d

# Node bridge accessible at:
#   http://127.0.0.1:9899
# Keycloak at:
#   http://localhost:8080/admin/
```

## Connection Examples

### iOS App
```swift
let bridge = AIBridgeService(serverHost: "127.0.0.1", serverPort: 9897)
```

### JavaScript — backend AI calls (python3_bridge.py)
```javascript
const ws  = new WebSocket('ws://127.0.0.1:9897');
const api = 'http://127.0.0.1:9897/api/health';
```

### JavaScript — frontend dashboard (server_9898.js)
```javascript
// Open the dashboard in a browser
window.location.href = 'http://127.0.0.1:9898';
```

### Terminal (a-Shell / iSH)
```bash
curl http://127.0.0.1:9897/api/health   # Python bridge health
curl http://127.0.0.1:9898/health       # Frontend server health
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `SG_PORT` | `9897` | Python bridge listen port |
| `PORT` (server_9898.js) | `9898` | KODER Frontend / Dashboard listen port |
| `PORT_UNIFIED` | `9899` | Unified_Server.js listen port |
| `NODE_BRIDGE_PORT` | `9899` | Node.js bridge listen port |
| `KEYCLOAK_URL` | `http://127.0.0.1:8080` | Keycloak base URL |

## Security Notes

1. **Single external surface per service**: Each service binds to one port only
2. **No Redis/Postgres host exposure**: Internal services via Docker network only
3. **Keycloak official ports**: 8080/8443 (standard ports)
4. **Air-gap compatible**: Python bridge has zero external dependencies
5. **Port conflict detection**: `/api/conflicts` endpoint checks for processes holding port 9897
