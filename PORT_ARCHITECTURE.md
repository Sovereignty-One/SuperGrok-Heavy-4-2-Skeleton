# Port Architecture - Unified Entry Point

## Overview

All services in the SuperGrok Heavy 4.2 Skeleton funnel through **port 9898** as the single external entry point. This eliminates "port zoo" chaos and provides a clean, secure architecture.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                  External Clients                            │
│  • iOS App (ws://127.0.0.1:9898)                            │
│  • React Frontend (http://127.0.0.1:9898)                   │
│  • a-shell/iSH Terminal (127.0.0.1:9898)                    │
└────────────────────┬────────────────────────────────────────┘
                     │
                     │ Port 9898 (ONLY external port)
                     ▼
┌─────────────────────────────────────────────────────────────┐
│              Node Bridge (Port 9898)                         │
│  • Single entry point for all traffic                       │
│  • WebSocket support: /ws/alerts                            │
│  • REST API proxy: /api/v1/* → Backend                      │
│  • Health check: /health                                    │
└────────────────────┬────────────────────────────────────────┘
                     │
                     │ Internal Docker Network Only
                     ▼
┌─────────────────────────────────────────────────────────────┐
│          Backend Services (Internal Only)                    │
│                                                              │
│  ┌──────────────────────────────────────────────┐          │
│  │  FastAPI Backend (Port 9898 internal)        │          │
│  │  • REST API endpoints                        │          │
│  │  • AI processing                             │          │
│  │  • Business logic                            │          │
│  └────────────┬─────────────────────────────────┘          │
│               │                                              │
│  ┌────────────┴─────────────┬───────────────────┐          │
│  │                          │                   │          │
│  ▼                          ▼                   ▼          │
│  Redis (6379)          PostgreSQL (5432)   Other Services  │
│  Internal only         Internal only       Internal only   │
│  127.0.0.1 bind       Docker network       Docker network  │
└─────────────────────────────────────────────────────────────┘
```

## Port Assignment

### External Ports (Exposed to Host)
- **9898**: Node Bridge (ONLY external port)
  - HTTP REST API
  - WebSocket connections
  - Proxies to all internal services

### Internal Ports (Docker Network Only)
- **9898**: FastAPI Backend (internal container port)
- **6379**: Redis (bound to 127.0.0.1, protected mode enabled)
- **5432**: PostgreSQL (internal database)

### Deprecated Ports (No Longer Used)
- ~~9899~~: Previously used for separate bridge, now unified with 9898
- ~~8080~~: Keycloak HTTP (not currently active)
- ~~8443~~: Keycloak HTTPS (not currently active)
- ~~9000~~: Management port (consolidated into 9898)

## Connection Examples

### iOS App (Swift)
```swift
// All services connect to unified port 9898
let apiClient = SovereigntyAPIClient(baseURL: "http://127.0.0.1:9898")
let aiBridge = AIBridgeService(serverHost: "127.0.0.1", serverPort: 9898)
let ttsService = CoquiTTSService(serverURL: "ws://127.0.0.1:9898")
```

### React Frontend (TypeScript)
```typescript
// WebSocket connection
const ws = new WebSocket('ws://127.0.0.1:9898/ws/alerts');

// API calls
const response = await fetch('http://127.0.0.1:9898/api/v1/endpoint');
```

### Node.js / Unified Server
```javascript
// Environment configuration
const PORT_UNIFIED = process.env.PORT_UNIFIED || '9898';
const PORT_BRIDGE  = process.env.PORT_BRIDGE  || '9898';
```

## Docker Compose Configuration

### Node Bridge (External Entry Point)
```yaml
node-bridge:
  build: ./node-bridge
  ports:
    - "9898:9898"  # ONLY external port mapping
  environment:
    - BACKEND_URL=http://backend:9898
    - NODE_BRIDGE_PORT=9898
  depends_on:
    - backend
```

### Backend (Internal Only)
```yaml
backend:
  build: ./backend
  expose:
    - "9898"  # Internal only, not published to host
  environment:
    - REDIS_URL=redis://redis:6379/0
  depends_on:
    - redis
    - db
```

### Redis (Internal Only, Secured)
```yaml
redis:
  image: redis:7
  command: redis-server --bind 127.0.0.1 --protected-mode yes
  expose:
    - "6379"  # Internal only, not published to host
```

### PostgreSQL (Internal Only)
```yaml
db:
  image: postgres:13
  expose:
    - "5432"  # Internal only, not published to host
  volumes:
    - db_data:/var/lib/postgresql/data
```

## Security Benefits

1. **Single Attack Surface**: Only port 9898 is exposed externally
2. **Internal Service Protection**: Redis, PostgreSQL, and Backend are not directly accessible
3. **Simplified Firewall Rules**: Only need to allow port 9898
4. **Localhost Binding**: Redis binds to 127.0.0.1 with protected mode enabled
5. **Network Isolation**: All internal services communicate via Docker network only

## Migration from Previous Architecture

### Old Architecture (Multiple Ports)
- Backend: 9898 (external)
- Node Bridge: 9899 (external)
- Redis: 6379 (external)
- PostgreSQL: 5432 (external)
- Potential Keycloak: 8080/8443

### New Architecture (Unified Port)
- **Single external port: 9898**
- All internal services isolated
- Node Bridge acts as reverse proxy
- Clean, secure, and simple

## Environment Variables

### Root .env
```bash
# Unified port configuration
PORT_UNIFIED=9898
PORT_BRIDGE=9898
PORT_AUTH=9898
```

### Sovereignty-AI-Studio-main/.env
```bash
# Backend configuration
BACKEND_PORT=9898
API_URL=http://localhost:9898
REDIS_URL=redis://redis:6379/0  # Internal Docker network
```

## Troubleshooting

### Can't connect to services
1. Verify Docker containers are running: `docker-compose ps`
2. Check node-bridge is listening on 9898: `netstat -tulpn | grep 9898`
3. Check container logs: `docker-compose logs node-bridge`

### Port already in use
```bash
# Find process using port 9898
lsof -i :9898

# Kill the process if needed
kill -9 <PID>
```

### Redis connection issues
Redis should NOT be accessible externally. It's internal-only via Docker network at `redis://redis:6379/0`.

### Backend not accessible
Backend should NOT be accessible externally. All traffic goes through node-bridge at port 9898.

## Testing the Architecture

### Health Check
```bash
curl http://127.0.0.1:9898/health
```

### WebSocket Test
```bash
# Using websocat (install: cargo install websocat)
websocat ws://127.0.0.1:9898/ws/alerts
```

### API Test
```bash
curl http://127.0.0.1:9898/api/v1/status
```

## Future Considerations

### Keycloak Integration (Optional)
If Keycloak is added in the future:
- Run Keycloak internally in Docker network
- Proxy through node-bridge at /auth/* path
- NO direct external ports (8080/8443)
- All auth flows via port 9898

### HTTPS/TLS
To add HTTPS:
- Terminate TLS at node-bridge (port 9898)
- Use Let's Encrypt or self-signed certificates
- Internal services remain HTTP
- Single certificate for port 9898

## Summary

✅ **One port to rule them all: 9898**
✅ **Clean architecture: Single external entry point**
✅ **Secure by default: Internal services isolated**
✅ **Simple configuration: No port juggling**
✅ **iOS/React/Terminal: All connect to 127.0.0.1:9898**

---

**Last Updated**: March 12, 2026
**Architecture Version**: 2.0 (Unified Port)
