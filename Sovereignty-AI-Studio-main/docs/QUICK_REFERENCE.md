# 🚨 Live Alerts Quick Reference

## Command Cheat Sheet

### Setup
```bash
# Initialize database
python init_db.py

# Run tests
python test_alerts.py

# Run demo
python demo_alerts.py
```

### Start Services
```bash
# Backend (Terminal 1)
cd backend
PYTHONPATH=./backend uvicorn app.main:app --reload

# Frontend (Terminal 2)
cd frontend
npm install && npm start
```

### API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/alerts/` | Create alert |
| GET | `/api/v1/alerts/` | List alerts |
| GET | `/api/v1/alerts/stats` | Get statistics |
| GET | `/api/v1/alerts/{id}` | Get specific alert |
| PATCH | `/api/v1/alerts/{id}/read` | Mark as read |
| PATCH | `/api/v1/alerts/{id}/dismiss` | Dismiss alert |
| POST | `/api/v1/alerts/mark-read` | Bulk mark as read |
| WS | `/api/v1/alerts/ws/{user_id}` | WebSocket connection |

### Alert Types

| Type | Usage | Severity |
|------|-------|----------|
| `info` | Informational messages | low |
| `warning` | Warnings needing attention | medium |
| `error` | Error notifications | high |
| `security` | General security alerts | high |
| `system` | System-level alerts | varies |
| `debugger_touch` | Debugger detected | critical |
| `chain_break` | Integrity violation | critical |
| `lie_detected` | Truth verification fail | high |
| `override_spoken` | Forbidden command | high |
| `yuva9v_tripped` | Emergency protocol | critical |

### Severity Levels

| Level | Behavior | Visual |
|-------|----------|--------|
| `low` | Auto-dismiss 5s | Blue border |
| `medium` | Auto-dismiss 10s | Yellow border |
| `high` | Manual dismiss | Orange border |
| `critical` | Manual dismiss | Red border + pulse |

### Quick Examples

#### Create Alert (Python)
```python
from app.services.alert_service import AlertService
from app.schemas.alert import AlertCreate
from app.core.database import SessionLocal

db = SessionLocal()
alert = AlertCreate(
    type="security",
    title="Unauthorized Access",
    message="Failed login attempt",
    severity="high",
    source="auth_system"
)
AlertService.create_alert(db, alert)
db.close()
```

#### Create Alert (curl)
```bash
curl -X POST "http://localhost:9898/api/v1/alerts/" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "info",
    "title": "Task Complete",
    "message": "Your task finished",
    "severity": "low"
  }'
```

#### Create Alert with Audio (curl)
```bash
curl -X POST "http://localhost:9898/api/v1/alerts/?speak=true" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "critical",
    "title": "CRITICAL ALERT",
    "message": "System failure detected",
    "severity": "critical"
  }'
```

#### Get Unread Alerts (curl)
```bash
curl "http://localhost:9898/api/v1/alerts/?unread_only=true&limit=10"
```

#### WebSocket (JavaScript)
```javascript
const ws = new WebSocket('ws://localhost:9898/api/v1/alerts/ws/1');

ws.onmessage = (event) => {
  const msg = JSON.parse(event.data);
  if (msg.type === 'alert') {
    console.log('New alert:', msg.data);
  }
};

// Keep-alive
setInterval(() => ws.send('ping'), 30000);
```

### Frontend Usage

#### Use WebSocket Hook
```typescript
import { useAlertWebSocket } from './hooks/useAlertWebSocket';

const { isConnected } = useAlertWebSocket({
  userId: 1,
  onAlert: (alert) => console.log(alert),
  autoReconnect: true
});
```

#### Call API
```typescript
import { AlertAPI } from './services/alertApi';

// Get alerts
const alerts = await AlertAPI.getAlerts({ unread_only: true });

// Create alert
await AlertAPI.createAlert({
  type: 'info',
  title: 'Hello',
  message: 'World',
  severity: 'low'
});

// Mark as read
await AlertAPI.markAsRead(alertId);
```

### Environment Variables

```bash
# Backend
DATABASE_URL=postgresql://user:pass@localhost/db
PIPER_MODEL_PATH=/path/to/model.onnx
PIPER_DIR=/path/to/piper-tts

# Frontend  
REACT_APP_API_URL=http://localhost:9898/api/v1
REACT_APP_WS_URL=ws://localhost:9898
```

### Troubleshooting

#### WebSocket won't connect
```bash
# Check backend is running
curl http://localhost:9898/health

# Check WebSocket endpoint
wscat -c ws://localhost:9898/api/v1/alerts/ws/1
```

#### Database issues
```bash
# Reinitialize
python init_db.py

# Check connection
psql -h localhost -U user -d dbname
```

#### TTS not working
```bash
# Test Piper
echo "test" | piper --model model.onnx --output test.wav

# Check environment
echo $PIPER_MODEL_PATH
```

### File Locations

```
Project Root
├── backend/
│   ├── app/
│   │   ├── api/v1/endpoints/alerts.py    # API endpoints
│   │   ├── models/alert.py                # Database model
│   │   ├── schemas/alert.py               # Pydantic schemas
│   │   ├── services/alert_service.py      # Business logic
│   │   ├── services/piper_tts_service.py  # TTS integration
│   │   └── core/websocket.py              # WebSocket manager
│   └── alembic/versions/001_add_alerts.py # Migration
├── frontend/
│   └── src/
│       ├── types/alert.ts                 # TypeScript types
│       ├── hooks/useAlertWebSocket.ts     # WebSocket hook
│       ├── services/alertApi.ts           # API service
│       └── components/alerts/             # React components
├── docs/
│   ├── ALERTS_USAGE.md                    # Usage guide
│   ├── PIPER_INTEGRATION.md               # TTS guide
│   └── IMPLEMENTATION_SUMMARY.md          # Summary
├── init_db.py                             # DB initialization
├── test_alerts.py                         # Tests
└── demo_alerts.py                         # Demo script
```

### Resources

- **Documentation**: `docs/ALERTS_USAGE.md`
- **TTS Guide**: `docs/PIPER_INTEGRATION.md`
- **API Docs**: `http://localhost:9898/docs` (when running)
- **Implementation**: `docs/IMPLEMENTATION_SUMMARY.md`

### Support

Issues? Check:
1. Backend logs
2. Browser console
3. Database connection
4. WebSocket status
5. Environment variables

---

**Quick Test**: Run `python demo_alerts.py` to verify everything works!
