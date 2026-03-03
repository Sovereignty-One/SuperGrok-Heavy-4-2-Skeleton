#!/usr/bin/env python3
"""
Test script for the alerts system
Tests creating alerts and verifying the connection
"""
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app.models.alert import Alert, AlertType
from app.schemas.alert import AlertCreate
from app.services.alert_service import AlertService
from app.core.database import SessionLocal

def test_alert_system():
    """Test the alert system functionality"""
    print("Testing Alerts System...")
    print("=" * 50)
    
    db = SessionLocal()
    
    try:
        # Test 1: Create a system alert
        print("\n1. Creating system alert...")
        system_alert = AlertCreate(
            type="system",
            title="System Test Alert",
            message="This is a test system alert",
            severity="low",
            source="test_script"
        )
        created_alert = AlertService.create_alert(db, system_alert)
        print(f"✓ System alert created with ID: {created_alert.id}")
        
        # Test 2: Create a security alert
        print("\n2. Creating security alert...")
        security_alert = AlertCreate(
            type="security",
            title="Security Test",
            message="Testing security alert functionality",
            severity="high",
            source="security_module"
        )
        created_security = AlertService.create_alert(db, security_alert)
        print(f"✓ Security alert created with ID: {created_security.id}")
        
        # Test 3: Get system alerts
        print("\n3. Fetching system alerts...")
        alerts = AlertService.get_system_alerts(db, limit=10)
        print(f"✓ Found {len(alerts)} system alerts")
        for alert in alerts[:3]:  # Show first 3
            print(f"   - [{alert.type.value}] {alert.title}")
        
        # Test 4: Mark alert as read
        print("\n4. Marking alert as read...")
        marked = AlertService.mark_as_read(db, created_alert.id)
        print(f"✓ Alert {marked.id} marked as read at {marked.read_at}")
        
        # Test 5: Get alert by ID
        print("\n5. Retrieving specific alert...")
        fetched = AlertService.get_alert(db, created_security.id)
        print(f"✓ Retrieved alert: {fetched.title}")
        print(f"   Type: {fetched.type.value}")
        print(f"   Severity: {fetched.severity}")
        print(f"   Read: {fetched.is_read}")
        
        print("\n" + "=" * 50)
        print("✓ All tests passed! Alert system is working.")
        
    except Exception as e:
        print(f"\n✗ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        db.close()

if __name__ == "__main__":
    test_alert_system()
