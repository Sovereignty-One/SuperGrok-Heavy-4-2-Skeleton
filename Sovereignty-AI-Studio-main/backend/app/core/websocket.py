from fastapi import WebSocket
from typing import Dict, Set
import json
import asyncio


class ConnectionManager:
    """Manages WebSocket connections for live alerts"""

    def __init__(self):
        # Map of user_id to set of WebSocket connections
        self.active_connections: Dict[int, Set[WebSocket]] = {}
        # System-wide connections (for admin/monitoring)
        self.system_connections: Set[WebSocket] = set()

    async def connect(self, websocket: WebSocket, user_id: int = None):
        """Connect a new WebSocket client"""
        await websocket.accept()
        
        if user_id:
            if user_id not in self.active_connections:
                self.active_connections[user_id] = set()
            self.active_connections[user_id].add(websocket)
        else:
            self.system_connections.add(websocket)

    def disconnect(self, websocket: WebSocket, user_id: int = None):
        """Disconnect a WebSocket client"""
        if user_id and user_id in self.active_connections:
            self.active_connections[user_id].discard(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
        else:
            self.system_connections.discard(websocket)

    async def send_personal_alert(self, user_id: int, alert_data: dict):
        """Send an alert to a specific user"""
        if user_id in self.active_connections:
            disconnected = set()
            for connection in self.active_connections[user_id]:
                try:
                    await connection.send_json({
                        "type": "alert",
                        "data": alert_data
                    })
                except Exception as e:
                    print(f"Error sending alert to user {user_id}: {e}")
                    disconnected.add(connection)
            
            # Clean up disconnected clients
            for connection in disconnected:
                self.disconnect(connection, user_id)

    async def send_system_alert(self, alert_data: dict):
        """Send a system-wide alert to all connected clients"""
        disconnected = set()
        
        # Send to all user connections
        for user_id, connections in list(self.active_connections.items()):
            for connection in connections:
                try:
                    await connection.send_json({
                        "type": "system_alert",
                        "data": alert_data
                    })
                except Exception:
                    disconnected.add((connection, user_id))
        
        # Send to system connections
        for connection in self.system_connections:
            try:
                await connection.send_json({
                    "type": "system_alert",
                    "data": alert_data
                })
            except Exception:
                disconnected.add((connection, None))
        
        # Clean up disconnected clients
        for connection, user_id in disconnected:
            self.disconnect(connection, user_id)

    async def broadcast_alert_update(self, user_id: int, alert_id: int, action: str):
        """Broadcast an alert update (read, dismissed, etc.)"""
        if user_id in self.active_connections:
            for connection in self.active_connections[user_id]:
                try:
                    await connection.send_json({
                        "type": "alert_update",
                        "data": {
                            "alert_id": alert_id,
                            "action": action
                        }
                    })
                except Exception:
                    pass

    def get_connection_count(self) -> dict:
        """Get the number of active connections"""
        return {
            "user_connections": sum(len(conns) for conns in self.active_connections.values()),
            "users_connected": len(self.active_connections),
            "system_connections": len(self.system_connections)
        }


# Global instance
alert_manager = ConnectionManager()
