# Port Architecture

## Overview

The SuperGrok Heavy 4.2 Skeleton uses a clear port separation:

- **Python bridge** (`python3_bridge.py`) on **9897** — primary server for iSH / macOS / Linux (no Node.js required)
- **KODER** (iOS code editor file server) on **9898** — Koder app HTTP server
- **Node.js bridge** (`Unified_Server.js` / `node-bridge`) on **9899** — Docker-based bridge service
- **Keycloak** on **8080** (HTTP) / **8443** (HTTPS) — SSO / Identity Provider
- Internal services (backend, Redis, PostgreSQL) are not exposed to the host

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                  External Clients                            │
│  • iOS App / iSH / macOS (ws://127.0.0.1:9897)             │
│  • SGHv119.html / FullDashboard.html (http://127.0.0.1:9897)│
│  • KODER editor (http://127.0.0.1:9898)                    │
│  • React Frontend / Docker clients (http://127.0.0.1:9899) │
│  • Keycloak admin (http://localhost:8080/admin/)            │
└──────┬──────────────────────────┬──────────────┬────────────┘
       │ Port 9897                │ Port 9899    │ Port 8080/8443
       ▼                          ▼              ▼
┌──────────────────┐  ┌─────────────────────┐  ┌──────────────┐
│ python3_bridge.py│  │  node-bridge        │  │  Keycloak    │
│ (pure Python 3)  │  │  (Node.js/Docker)   │  │  (SSO/IdP)   │
│ • Serves HTML    │  │  • REST API proxy   │  │  • Auth      │
│ • WebSocket bus  │  │  • WebSocket relay  │  │  • OIDC/SAML │
│ • AI/key/audit   │  │  • /api/v1/*        │  └──────────────┘
└──────────────────┘  └──────────┬──────────┘
                                 │ Internal Docker Network
                                 ▼
              ┌──────────────────────────────────────┐
              │  FastAPI Backend (9898 internal)     │
              │  • REST API endpoints                │
              │  • AI processing / business logic    │
              └──────┬────────────────┬──────────────┘
                     ▼                ▼
              Redis (6379)     PostgreSQL (5432)
              Internal only    Internal only
              127.0.0.1 bind   Docker network
```

## Port Assignment

### External Ports (Exposed to Host)
- **9897**: Python bridge (`python3_bridge.py`) — standalone/iSH server
  - Serves `SGHv119.html` and other dashboard HTML
  - WebSocket AI/agent bus
  - API routes: `/api/health`, `/api/ai`, `/api/keys`, `/api/speak`, `/api/audit`, `/api/rotate-key`, `/api/conflicts`
- **9898**: KODER — iOS code editor file server
- **9899**: Node.js bridge (`node-bridge` / `Unified_Server.js`) — Docker service
  - REST API proxy to FastAPI backend
  - WebSocket relay
- **8080**: Keycloak HTTP — admin console at `http://localhost:8080/admin/`
- **8443**: Keycloak HTTPS/TLS — configure `KC_HTTPS_CERTIFICATE_FILE` / `KC_HTTPS_CERTIFICATE_KEY_FILE`

### Internal Ports (Docker Network Only)
- **9898**: FastAPI Backend (internal container port, not published to host)
- **6379**: Redis (bound to 127.0.0.1, protected mode enabled)
- **5432**: PostgreSQL (internal database, Docker network only)

## Quick Start

### Standalone (iSH / macOS / Linux — no Docker)
```bash
# Set API keys
export ANTHROPIC_API_KEY=sk-ant-...
export OPENAI_API_KEY=sk-...
export GROK_API_KEY=xai-...

# Run Python bridge
python3 python3_bridge.py
# → http://127.0.0.1:9897

# Or use start-dashboard.sh
./start-dashboard.sh
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

### JavaScript (SGHv119.html)
```javascript
const ws = new WebSocket('ws://127.0.0.1:9897');
const api = 'http://127.0.0.1:9897/api/health';
```

### Terminal (a-Shell / iSH)
```bash
curl http://127.0.0.1:9897/api/health
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `SG_PORT` | `9897` | Python bridge listen port |
| `NODE_BRIDGE_PORT` | `9899` | Node.js bridge listen port |
| `PORT_UNIFIED` | `9899` | Unified_Server.js listen port |
| `KEYCLOAK_URL` | `http://127.0.0.1:8080` | Keycloak base URL |
| `BACKEND_URL` | `http://127.0.0.1:9897` | Backend URL for node-bridge |

## Security Notes

1. **Single external surface per service**: Each service binds to one port only
2. **No Redis/Postgres exposure**: Internal services communicate via Docker network only
3. **Keycloak official ports**: 8080/8443 (not custom ports)
4. **Air-gap compatible**: Python bridge has zero external dependencies
5. **Port conflict detection**: `/api/conflicts` endpoint checks for Node.js holding port 9897
