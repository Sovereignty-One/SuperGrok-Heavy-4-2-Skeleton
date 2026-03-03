# Live Alerts System - Usage Guide

## Overview

The Live Alerts System provides real-time notifications for security events, system status, and user-defined alerts across the Sovereignty AI Studio platform.

## Architecture

### Backend (Python/FastAPI)
- **WebSocket Server**: Real-time bidirectional communication
- **REST API**: CRUD operations for alerts
- **Database**: PostgreSQL with SQLAlchemy ORM
- **TTS Integration**: Piper for audio notifications

### Frontend (React/TypeScript)
- **WebSocket Client**: Auto-reconnecting real-time connection
- **Toast Notifications**: Non-intrusive alert display
- **Alert Center**: Comprehensive alert management panel
- **Header Badge**: Unread count indicator

## Alert Types

### Standard Types
- `info` - Informational messages
- `warning` - Warning messages requiring attention
- `error` - Error notifications
- `system` - System-level alerts
- `security` - General security alerts

### Security-Specific Types
- `debugger_touch` - Debugger attachment detected
- `chain_break` - Integrity chain violation
- `lie_detected` - Truth verification failure
- `override_spoken` - Forbidden command detected
- `yuva9v_tripped` - Emergency shutdown protocol

## Severity Levels

- **low**: Informational, auto-closes after 5 seconds
- **medium**: Requires acknowledgment, auto-closes after 10 seconds
- **high**: Important, requires manual dismissal
- **critical**: Urgent, persistent until dismissed, pulsing animation

## API Reference

### Create Alert

**Endpoint:** `POST /api/v1/alerts/`

**Parameters:**
- `speak` (query, optional): Enable TTS for the alert

**Request Body:**
```json
{
  "type": "security",
  "title": "Unauthorized Access",
  "message": "Multiple failed login attempts detected from IP 192.168.1.100",
  "severity": "high",
  "source": "auth_module",
  "action_url": "/security/logs",
  "metadata": "{\"ip\": \"192.168.1.100\", \"attempts\": 5}"
}
```

**Response:**
```json
{
  "id": 42,
  "user_id": 1,
  "type": "security",
  "title": "Unauthorized Access",
  "message": "Multiple failed login attempts...",
  "severity": "high",
  "source": "auth_module",
  "is_read": false,
  "is_dismissed": false,
  "created_at": "2026-02-12T22:00:00Z",
  "read_at": null,
  "dismissed_at": null
}
```

### Get Alerts

**Endpoint:** `GET /api/v1/alerts/`

**Query Parameters:**
- `skip` (int): Number of alerts to skip for pagination
- `limit` (int): Maximum number of alerts to return (1-100)
- `unread_only` (bool): Return only unread alerts
- `alert_type` (string): Filter by alert type

**Example:**
```bash
GET /api/v1/alerts/?unread_only=true&limit=20
```

### Get Alert Statistics

**Endpoint:** `GET /api/v1/alerts/stats`

**Response:**
```json
{
  "total": 150,
  "unread": 12,
  "by_type": {
    "security": 45,
    "system": 30,
    "info": 75
  },
  "by_severity": {
    "critical": 5,
    "high": 20,
    "medium": 75,
    "low": 50
  }
}
```

### Mark Alert as Read

**Endpoint:** `PATCH /api/v1/alerts/{alert_id}/read`

### Dismiss Alert

**Endpoint:** `PATCH /api/v1/alerts/{alert_id}/dismiss`

### Mark Multiple as Read

**Endpoint:** `POST /api/v1/alerts/mark-read`

**Request Body:**
```json
[1, 2, 3, 4, 5]
```

## WebSocket API

### Connection

Connect to: `ws://localhost:9898/api/v1/alerts/ws/{user_id}`

### Message Types

**Incoming Alert:**
```json
{
  "type": "alert",
  "data": {
    "id": 42,
    "title": "Security Alert",
    "message": "...",
    ...
  }
}
```

**System Alert:**
```json
{
  "type": "system_alert",
  "data": {
    "id": 43,
    "title": "System Maintenance",
    ...
  }
}
```

**Alert Update:**
```json
{
  "type": "alert_update",
  "data": {
    "alert_id": 42,
    "action": "read"  // or "dismissed"
  }
}
```

### Keep-Alive

Send `"ping"` to keep the connection alive. Server responds with `"pong"`.

## Frontend Integration

### Using the AlertAPI Service

```typescript
import { AlertAPI } from './services/alertApi';

// Get alerts
const alerts = await AlertAPI.getAlerts({
  unread_only: true,
  limit: 50
});

// Create alert
const newAlert = await AlertAPI.createAlert({
  type: 'info',
  title: 'Task Complete',
  message: 'Your AI task has finished processing',
  severity: 'low'
});

// Mark as read
await AlertAPI.markAsRead(alertId);

// Dismiss
await AlertAPI.dismissAlert(alertId);
```

### Using the WebSocket Hook

```typescript
import { useAlertWebSocket } from './hooks/useAlertWebSocket';

function MyComponent() {
  const { isConnected } = useAlertWebSocket({
    userId: currentUser.id,
    onAlert: (alert) => {
      console.log('New alert:', alert);
      // Handle new alert
    },
    onSystemAlert: (alert) => {
      console.log('System alert:', alert);
      // Handle system alert
    },
    autoReconnect: true
  });

  return (
    <div>
      {isConnected ? 'Connected' : 'Disconnected'}
    </div>
  );
}
```

## Integration with Security Modules

### From Python Code

```python
from app.services.alert_service import AlertService
from app.schemas.alert import AlertCreate
from app.core.database import SessionLocal

# Create an alert
db = SessionLocal()
alert = AlertCreate(
    type="debugger_touch",
    title="Debugger Detected",
    message="Foreign debugger attached to process",
    severity="critical",
    source="security_monitor"
)
AlertService.create_alert(db, alert)
db.close()
```

### From Rust Code (src/security/Alerts.Rust)

The Rust security module can trigger alerts through the API:

```rust
// Call Python API via HTTP
let client = reqwest::Client::new();
client.post("http://localhost:9898/api/v1/alerts/")
    .json(&json!({
        "type": "chain_break",
        "title": "CHAIN BROKEN",
        "message": "Integrity failure. Session dead.",
        "severity": "critical",
        "source": "rust_security"
    }))
    .send()
    .await?;
```

## Best Practices

### 1. Alert Creation
- Use appropriate severity levels
- Provide actionable messages
- Include source information for debugging
- Use action_url for links to detailed views
- Store additional context in metadata field

### 2. Performance
- Batch mark-as-read operations when possible
- Use pagination for large alert lists
- Filter by unread_only when appropriate
- Implement alert retention policies

### 3. User Experience
- Critical alerts should not auto-dismiss
- Use TTS sparingly for important alerts only
- Provide clear dismiss/read actions
- Group related alerts when possible

### 4. Security
- Validate user access to alerts
- Sanitize alert content before display
- Log alert creation for audit trails
- Implement rate limiting for alert creation

## Troubleshooting

### WebSocket Won't Connect
1. Check backend is running: `curl http://localhost:9898/health`
2. Verify WebSocket URL in frontend env: `REACT_APP_WS_URL`
3. Check browser console for errors
4. Verify user authentication token is valid

### Alerts Not Appearing
1. Check database connection
2. Verify user_id is correct
3. Check browser console for WebSocket messages
4. Verify alert wasn't auto-dismissed

### TTS Not Working
1. Verify Piper is installed and in PATH
2. Check PIPER_MODEL_PATH environment variable
3. Test Piper manually: `echo "test" | piper --model path/to/model.onnx --output test.wav`
4. Verify audio system is working

### High Memory Usage
1. Implement alert cleanup/archival
2. Reduce WebSocket message frequency
3. Limit toast notification count
4. Use pagination more aggressively

## Examples

### Example 1: Security Event

```python
# Detect and alert on security event
AlertService.create_alert(db, AlertCreate(
    type="security",
    title="Suspicious Activity",
    message=f"User {username} accessed restricted resource",
    severity="high",
    source="access_control",
    action_url=f"/security/audit?user={user_id}",
    metadata=json.dumps({
        "user_id": user_id,
        "resource": resource_path,
        "timestamp": datetime.now().isoformat()
    })
))
```

### Example 2: System Monitoring

```python
# Monitor system health and alert on issues
if cpu_usage > 90:
    AlertService.create_alert(db, AlertCreate(
        type="warning",
        title="High CPU Usage",
        message=f"CPU usage at {cpu_usage}%",
        severity="medium",
        source="system_monitor"
    ))
```

### Example 3: User Notification

```python
# Notify user of task completion
AlertService.create_alert(db, AlertCreate(
    user_id=user.id,
    type="info",
    title="Processing Complete",
    message="Your AI model training has completed successfully",
    severity="low",
    source="ml_pipeline",
    action_url="/models/training-history"
))
```

## Future Enhancements

- [ ] Alert grouping and aggregation
- [ ] Custom alert sounds per severity
- [ ] Email/SMS notifications for critical alerts
- [ ] Alert templates and presets
- [ ] Advanced filtering and search
- [ ] Alert analytics and reporting
- [ ] Multi-language support
- [ ] Mobile push notifications
- [ ] Alert scheduling and snoozing
- [ ] Integration with external monitoring tools
