#!/usr/bin/env python3
"""
Live Alerts System Demo
Demonstrates the alerts functionality by creating various types of alerts
"""
import sys
import os
import time
import asyncio

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app.models.alert import Alert, AlertType
from app.schemas.alert import AlertCreate
from app.services.alert_service import AlertService
from app.core.database import SessionLocal
from app.core.websocket import alert_manager


def demo_create_alerts():
    """Create sample alerts to demonstrate the system"""
    print("🚨 Live Alerts System Demo")
    print("=" * 60)
    
    db = SessionLocal()
    
    try:
        alerts_data = [
            {
                "type": "info",
                "title": "System Started",
                "message": "Sovereignty AI Studio initialized successfully",
                "severity": "low",
                "source": "system"
            },
            {
                "type": "security",
                "title": "Security Scan Complete",
                "message": "All systems passed security validation",
                "severity": "medium",
                "source": "security_scanner"
            },
            {
                "type": "warning",
                "title": "High Memory Usage",
                "message": "Memory usage at 85% - consider optimizing workload",
                "severity": "medium",
                "source": "system_monitor"
            },
            {
                "type": "debugger_touch",
                "title": "DEBUGGER DETECTED",
                "message": "Foreign debugger attached. Killing process.",
                "severity": "critical",
                "source": "security_module"
            },
            {
                "type": "lie_detected",
                "title": "LIE DETECTED",
                "message": "Truth probe failed. Trust revoked for session.",
                "severity": "high",
                "source": "ai_lie_detector"
            },
            {
                "type": "system",
                "title": "Backup Complete",
                "message": "System backup completed successfully at 22:00 UTC",
                "severity": "low",
                "source": "backup_system"
            }
        ]
        
        print(f"\n📋 Creating {len(alerts_data)} sample alerts...\n")
        
        created_alerts = []
        for i, alert_data in enumerate(alerts_data, 1):
            alert_schema = AlertCreate(**alert_data)
            alert = AlertService.create_alert(db, alert_schema)
            created_alerts.append(alert)
            
            # Display created alert
            severity_emoji = {
                "low": "ℹ️",
                "medium": "⚠️",
                "high": "🔥",
                "critical": "🚨"
            }
            emoji = severity_emoji.get(alert.severity, "📢")
            
            print(f"{i}. {emoji} [{alert.type.value.upper()}] {alert.title}")
            print(f"   Message: {alert.message}")
            print(f"   Severity: {alert.severity}")
            print(f"   Source: {alert.source}")
            print(f"   ID: {alert.id}")
            print()
            
            # Small delay for dramatic effect
            time.sleep(0.5)
        
        # Get statistics
        print("\n📊 Alert Statistics:")
        print("-" * 60)
        
        system_alerts = AlertService.get_system_alerts(db, limit=100)
        unread_count = len([a for a in system_alerts if not a.is_read])
        
        print(f"Total Alerts: {len(system_alerts)}")
        print(f"Unread: {unread_count}")
        print(f"Read: {len(system_alerts) - unread_count}")
        
        # Count by type
        type_counts = {}
        for alert in system_alerts:
            alert_type = alert.type.value
            type_counts[alert_type] = type_counts.get(alert_type, 0) + 1
        
        print("\nBy Type:")
        for alert_type, count in sorted(type_counts.items()):
            print(f"  {alert_type}: {count}")
        
        # Count by severity
        severity_counts = {}
        for alert in system_alerts:
            severity = alert.severity
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
        
        print("\nBy Severity:")
        for severity, count in sorted(severity_counts.items()):
            print(f"  {severity}: {count}")
        
        print("\n" + "=" * 60)
        print("✅ Demo complete!")
        print("\nTo view these alerts:")
        print("  1. Start the backend: cd backend && uvicorn app.main:app --reload")
        print("  2. Start the frontend: cd frontend && npm start")
        print("  3. Open http://localhost:9898 and click the bell icon")
        print("\nOr query via API:")
        print("  curl http://localhost:9898/api/v1/alerts/")
        
        return created_alerts
        
    except Exception as e:
        print(f"\n❌ Error during demo: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        db.close()


def demo_mark_as_read():
    """Demo marking alerts as read"""
    print("\n\n🔵 Marking first 3 alerts as read...")
    print("-" * 60)
    
    db = SessionLocal()
    try:
        alerts = AlertService.get_system_alerts(db, limit=3)
        for alert in alerts:
            if not alert.is_read:
                AlertService.mark_as_read(db, alert.id)
                print(f"✓ Marked alert {alert.id} as read: {alert.title}")
        print("Done!")
    finally:
        db.close()


def demo_websocket_status():
    """Show WebSocket connection manager status"""
    print("\n\n🌐 WebSocket Connection Status:")
    print("-" * 60)
    
    status = alert_manager.get_connection_count()
    print(f"Active user connections: {status['user_connections']}")
    print(f"Users connected: {status['users_connected']}")
    print(f"System connections: {status['system_connections']}")
    
    if status['user_connections'] == 0:
        print("\n💡 Tip: Start the frontend to see live WebSocket connections")


if __name__ == "__main__":
    # Run the demo
    demo_create_alerts()
    demo_mark_as_read()
    demo_websocket_status()
    
    print("\n" + "=" * 60)
    print("🎉 Live Alerts System is ready to use!")
    print("=" * 60)
