# Port Architecture

## Overview

The SuperGrok Heavy 4.2 Skeleton uses a clear port separation:

- **Python bridge** (`python3_bridge.py`) on **9898** — primary server for iSH / macOS / Linux (no Node.js required)
- **Node.js bridge** (`node-bridge`) on **9899** — Docker-based bridge service
- **Keycloak** on **8080** (HTTP) / **8443** (HTTPS) — SSO / Identity Provider
- Internal services (backend, Redis, PostgreSQL) are not exposed to the host

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                  External Clients                            │
│  • iOS App / iSH / macOS (ws://127.0.0.1:9898)             │
│  • SGHv119.html / FullDashboard.html (http://127.0.0.1:9898)│
│  • React Frontend / Docker clients (http://127.0.0.1:9899) │
│  • Keycloak admin (http://localhost:8080/admin/)            │
└──────┬──────────────────────────┬──────────────┬────────────┘
       │ Port 9898                │ Port 9899    │ Port 8080/8443
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
- **9898**: Python bridge (`python3_bridge.py`) — standalone/iSH server
  - Serves `SGHv119.html` and other dashboard HTML
  - WebSocket AI/agent bus
  - API routes: `/api/health`, `/api/ai`, `/api/keys`, `/api/speak`, `/api/audit`, `/api/rotate-key`, `/api/conflicts`
- **9899**: Node.js bridge (`node-bridge`) — Docker service
  - REST API proxy to FastAPI backend
  - WebSocket relay
- **8080**: Keycloak HTTP — admin console at `http://localhost:8080/admin/`
- **8443**: Keycloak HTTPS/TLS — configure `KC_HTTPS_CERTIFICATE_FILE` / `KC_HTTPS_CERTIFICATE_KEY_FILE`

### Internal Ports (Docker Network Only)
- **9898**: FastAPI Backend (internal container port, not published to host)
- **6379**: Redis (bound to 127.0.0.1, protected mode enabled)
- **5432**: PostgreSQL (internal database, Docker network only)

### Deprecated Ports
- ~9899 as unified entry~: Node.js bridge previously conflicted with Python bridge at 9898; now separated to 9899.

## Connection Examples

### iSH / macOS / Linux (Python bridge, port 9898)
```javascript
// Dashboard served directly from python3_bridge.py
// Access at: http://127.0.0.1:9898/

// WebSocket AI bus
const ws = new WebSocket('ws://127.0.0.1:9898');

// API calls
fetch('http://127.0.0.1:9898/api/ai', {
  method: 'POST',
  body: JSON.stringify({ agent: 'claude', prompt: 'Hello' })
});
```

### iOS App (Swift)
```swift
// Connect to Python bridge on port 9898
let apiClient = SovereigntyAPIClient(baseURL: "http://127.0.0.1:9898")
let aiBridge = AIBridgeService(serverHost: "127.0.0.1", serverPort: 9898)
let ttsService = CoquiTTSService(serverURL: "ws://127.0.0.1:9898")
```

### Docker / Node.js Bridge (port 9899)
```typescript
// WebSocket connection (Node.js bridge)
const ws = new WebSocket('ws://127.0.0.1:9899/ws/alerts');

// API calls via Node bridge
const response = await fetch('http://127.0.0.1:9899/api/v1/endpoint');
```

### Node.js / Unified Server
```javascript
// Environment configuration
const PORT_UNIFIED = process.env.PORT_UNIFIED || '9898';  // Python bridge
const PORT_BRIDGE  = process.env.PORT_BRIDGE  || '9899';  // Node.js bridge
```


## Docker Compose Configuration

### Root docker-compose.yml
```yaml
services:
  backend:
    build: ./backend
    ports:
      - "9898:9898"   # Python bridge / backend

  frontend:
    build: ./frontend
    ports:
      - "9899:9899"   # Node.js bridge

  keycloak:
    image: quay.io/keycloak/keycloak:26.0
    ports:
      - "8080:8080"   # Keycloak HTTP
      - "8443:8443"   # Keycloak HTTPS

  redis:
    image: redis:7
    ports:
      - "6379:6379"
```

### Sovereignty-AI-Studio-main/docker-compose.yml
```yaml
services:
  node-bridge:
    build: ./node-bridge
    ports:
      - "9899:9899"   # Node.js bridge (external)
    environment:
      - BACKEND_URL=http://backend:9898
      - NODE_BRIDGE_PORT=9899

  backend:
    build: ./backend
    expose:
      - "9898"        # Internal only, not published to host

  keycloak:
    image: quay.io/keycloak/keycloak:26.0
    ports:
      - "8080:8080"
      - "8443:8443"

  redis:
    image: redis:7
    command: redis-server --bind 127.0.0.1 --protected-mode yes
    expose:
      - "6379"        # Internal only

  db:
    image: postgres:13
    expose:
      - "5432"        # Internal only
```


## Security Benefits

1. **Separation of Concerns**: Python bridge (9898) and Node.js bridge (9899) serve distinct client types
2. **Internal Service Protection**: Redis, PostgreSQL, and FastAPI backend are not directly accessible
3. **Keycloak Isolation**: SSO runs as a dedicated service on its own ports (8080/8443)
4. **Localhost Binding**: Redis binds to 127.0.0.1 with protected mode enabled
5. **Network Isolation**: All internal services communicate via Docker network only

## Migration from Previous Architecture

### Old Architecture (v1.3 — "Unified 9898")
- Node Bridge: 9898 (external, conflicted with Python bridge)
- Backend: 9898 (external)
- Redis: 9898 (no port isolation)
- No Keycloak

### New Architecture (v1.4 — Separated Ports)
- **Python bridge**: 9898 (external) — iSH/macOS/Linux, no Node.js
- **Node.js bridge**: 9899 (external) — Docker, proxies to backend
- **Keycloak**: 8080 / 8443 (external) — dedicated SSO service
- **FastAPI backend**: internal only
- **Redis**: 6379 internal (127.0.0.1 bind, protected mode)
- **PostgreSQL**: 5432 internal (Docker network only)

## Environment Variables

### Root `.env`
```bash
# Python bridge (iSH / macOS / Linux)
PORT_UNIFIED=9898

# Node.js bridge (Docker)
PORT_BRIDGE=9899

# Auth port (Python bridge)
PORT_AUTH=9898

# Keycloak
KEYCLOAK_URL=http://localhost:8080
KEYCLOAK_REALM=sovereignty
KEYCLOAK_CLIENT_ID=sovereignty-app
```

### `Sovereignty-AI-Studio-main/.env`
```bash
# Backend (internal Docker port)
BACKEND_PORT=9898

# Node bridge external port
NODE_BRIDGE_PORT=9899

# Redis (internal Docker network)
REDIS_URL=redis://redis:6379/0

# Keycloak (internal Docker network)
KEYCLOAK_URL=http://keycloak:8080
```


## Troubleshooting

### Can't connect to Python bridge (port 9898)
```bash
# Check if python3_bridge.py is running
ps aux | grep python3_bridge
# Restart
sh start-dashboard.sh
```

### Can't connect to Node.js bridge (port 9899)
```bash
# Verify Docker containers are running
docker-compose ps
# Check logs
docker-compose logs node-bridge
# Verify port
netstat -tulpn | grep 9899
```

### Port already in use
```bash
# Find process using port 9898 or 9899
lsof -i :9898
lsof -i :9899
# Kill the process if needed
kill -9 <PID>
```

### Redis connection issues
Redis should NOT be accessible externally. It's internal-only via Docker network at `redis://redis:6379/0`.

### Backend not accessible
Backend should NOT be accessible externally. All traffic goes through node-bridge (9899) or python3_bridge.py (9898).

## Testing the Architecture

### Python Bridge (port 9898)
```bash
# Health check
curl http://127.0.0.1:9898/api/health

# WebSocket test
websocat ws://127.0.0.1:9898
```

### Node.js Bridge (port 9899)
```bash
# Health check
curl http://127.0.0.1:9899/health

# API test
curl http://127.0.0.1:9899/api/v1/status

# WebSocket test
websocat ws://127.0.0.1:9899/ws/alerts
```

### Keycloak
```bash
# Admin console (browser)
open http://localhost:8080/admin/
```

## Future Considerations

### HTTPS/TLS
To add HTTPS:
- Terminate TLS at node-bridge (port 9899)
- Or at python3_bridge.py (port 9898) for standalone setups
- Internal services remain HTTP
- Keycloak HTTPS via port 8443 (configure `KC_HTTPS_CERTIFICATE_FILE`)

## Summary

✅ **Python bridge on 9898**: iSH / macOS / Linux, no Node.js required  
✅ **Node.js bridge on 9899**: Docker-based, proxies to FastAPI backend  
✅ **Keycloak on 8080/8443**: Dedicated SSO/IdP service  
✅ **Internal services isolated**: Redis (6379), PostgreSQL (5432), FastAPI backend not exposed  
✅ **No port conflicts**: Python and Node.js bridges clearly separated  

---

**Last Updated**: April 14, 2026  
**Architecture Version**: 2.1 (Separated Ports + Keycloak)
