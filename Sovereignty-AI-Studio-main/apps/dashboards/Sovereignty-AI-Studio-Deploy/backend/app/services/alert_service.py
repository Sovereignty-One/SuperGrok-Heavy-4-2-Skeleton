from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from app.models.alert import Alert, AlertType
from app.schemas.alert import AlertCreate, AlertUpdate
from typing import List, Optional
from datetime import datetime


class AlertService:
    """Service for managing alerts"""

    @staticmethod
    def create_alert(db: Session, alert: AlertCreate) -> Alert:
        """Create a new alert"""
        db_alert = Alert(
            user_id=alert.user_id,
            type=alert.type,
            title=alert.title,
            message=alert.message,
            source=alert.source,
            severity=alert.severity,
            action_url=alert.action_url,
            metadata=alert.metadata,
        )
        db.add(db_alert)
        db.commit()
        db.refresh(db_alert)
        return db_alert

    @staticmethod
    def get_alert(db: Session, alert_id: int) -> Optional[Alert]:
        """Get a single alert by ID"""
        return db.query(Alert).filter(Alert.id == alert_id).first()

    @staticmethod
    def get_user_alerts(
        db: Session,
        user_id: int,
        skip: int = 0,
        limit: int = 50,
        unread_only: bool = False,
        alert_type: Optional[AlertType] = None,
    ) -> List[Alert]:
        """Get alerts for a specific user with filters"""
        query = db.query(Alert).filter(Alert.user_id == user_id)
        
        if unread_only:
            query = query.filter(Alert.is_read == False)
        
        if alert_type:
            query = query.filter(Alert.type == alert_type)
        
        query = query.filter(Alert.is_dismissed == False)
        query = query.order_by(desc(Alert.created_at))
        
        return query.offset(skip).limit(limit).all()

    @staticmethod
    def get_system_alerts(
        db: Session,
        skip: int = 0,
        limit: int = 50,
    ) -> List[Alert]:
        """Get system-wide alerts (no user_id)"""
        query = db.query(Alert).filter(Alert.user_id == None)
        query = query.filter(Alert.is_dismissed == False)
        query = query.order_by(desc(Alert.created_at))
        
        return query.offset(skip).limit(limit).all()

    @staticmethod
    def count_unread_alerts(db: Session, user_id: int) -> int:
        """Count unread alerts for a user"""
        return db.query(Alert).filter(
            Alert.user_id == user_id,
            Alert.is_read == False,
            Alert.is_dismissed == False
        ).count()

    @staticmethod
    def mark_as_read(db: Session, alert_id: int) -> Optional[Alert]:
        """Mark an alert as read"""
        alert = db.query(Alert).filter(Alert.id == alert_id).first()
        if alert and not alert.is_read:
            alert.is_read = True
            alert.read_at = datetime.utcnow()
            db.commit()
            db.refresh(alert)
        return alert

    @staticmethod
    def mark_multiple_as_read(db: Session, alert_ids: List[int]) -> int:
        """Mark multiple alerts as read"""
        count = db.query(Alert).filter(Alert.id.in_(alert_ids)).update(
            {Alert.is_read: True, Alert.read_at: datetime.utcnow()},
            synchronize_session=False
        )
        db.commit()
        return count

    @staticmethod
    def dismiss_alert(db: Session, alert_id: int) -> Optional[Alert]:
        """Dismiss an alert"""
        alert = db.query(Alert).filter(Alert.id == alert_id).first()
        if alert:
            alert.is_dismissed = True
            alert.dismissed_at = datetime.utcnow()
            db.commit()
            db.refresh(alert)
        return alert

    @staticmethod
    def get_alert_stats(db: Session, user_id: int) -> dict:
        """Get alert statistics for a user"""
        total = db.query(Alert).filter(
            Alert.user_id == user_id,
            Alert.is_dismissed == False
        ).count()
        
        unread = db.query(Alert).filter(
            Alert.user_id == user_id,
            Alert.is_read == False,
            Alert.is_dismissed == False
        ).count()
        
        by_type = dict(
            db.query(Alert.type, func.count(Alert.id))
            .filter(Alert.user_id == user_id, Alert.is_dismissed == False)
            .group_by(Alert.type)
            .all()
        )
        
        by_severity = dict(
            db.query(Alert.severity, func.count(Alert.id))
            .filter(Alert.user_id == user_id, Alert.is_dismissed == False)
            .group_by(Alert.severity)
            .all()
        )
        
        return {
            "total": total,
            "unread": unread,
            "by_type": {k.value: v for k, v in by_type.items()},
            "by_severity": by_severity,
        }
