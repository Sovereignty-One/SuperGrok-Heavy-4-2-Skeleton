from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.database import get_db
from app.core.websocket import alert_manager
from app.services.alert_service import AlertService
from app.services.piper_tts_service import piper_service
from app.schemas.alert import Alert, AlertCreate, AlertUpdate, AlertList, AlertStats
from app.models.alert import AlertType
from app.dependencies import get_current_user
from app.models.user import User
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


@router.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: int):
    """WebSocket endpoint for real-time alerts"""
    await alert_manager.connect(websocket, user_id)
    try:
        while True:
            # Keep connection alive and handle incoming messages
            data = await websocket.receive_text()
            # Could handle ping/pong or other commands here
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        alert_manager.disconnect(websocket, user_id)


@router.post("/", response_model=Alert)
def create_alert(
    alert: AlertCreate,
    speak: bool = Query(False, description="Enable text-to-speech for this alert"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new alert with optional TTS"""
    # If no user_id specified, use current user
    if alert.user_id is None:
        alert.user_id = current_user.id
    
    db_alert = AlertService.create_alert(db, alert)
    
    # Send real-time notification
    import asyncio
    from app.schemas.alert import Alert as AlertSchema
    alert_data = AlertSchema.model_validate(db_alert).model_dump(mode='json')
    
    if db_alert.user_id:
        asyncio.create_task(alert_manager.send_personal_alert(db_alert.user_id, alert_data))
    else:
        asyncio.create_task(alert_manager.send_system_alert(alert_data))
    
    # Optional: Speak the alert using Piper TTS
    if speak:
        try:
            piper_service.speak_alert(
                alert_title=db_alert.title,
                alert_message=db_alert.message,
                severity=db_alert.severity
            )
        except Exception as e:
            logger.warning(f"Failed to speak alert: {e}")
    
    return db_alert


@router.get("/", response_model=List[Alert])
def get_alerts(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    unread_only: bool = Query(False),
    alert_type: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get alerts for the current user"""
    alert_type_enum = None
    if alert_type:
        try:
            alert_type_enum = AlertType[alert_type.upper()]
        except KeyError:
            raise HTTPException(status_code=400, detail="Invalid alert type")
    
    alerts = AlertService.get_user_alerts(
        db=db,
        user_id=current_user.id,
        skip=skip,
        limit=limit,
        unread_only=unread_only,
        alert_type=alert_type_enum,
    )
    return alerts


@router.get("/stats", response_model=AlertStats)
def get_alert_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get alert statistics for the current user"""
    stats = AlertService.get_alert_stats(db, current_user.id)
    return stats


@router.get("/{alert_id}", response_model=Alert)
def get_alert(
    alert_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a specific alert"""
    alert = AlertService.get_alert(db, alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    if alert.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to access this alert")
    
    return alert


@router.patch("/{alert_id}/read", response_model=Alert)
def mark_alert_as_read(
    alert_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Mark an alert as read"""
    alert = AlertService.get_alert(db, alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    if alert.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to access this alert")
    
    updated_alert = AlertService.mark_as_read(db, alert_id)
    
    # Broadcast update
    import asyncio
    asyncio.create_task(alert_manager.broadcast_alert_update(current_user.id, alert_id, "read"))
    
    return updated_alert


@router.patch("/{alert_id}/dismiss", response_model=Alert)
def dismiss_alert(
    alert_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Dismiss an alert"""
    alert = AlertService.get_alert(db, alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    if alert.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to access this alert")
    
    updated_alert = AlertService.dismiss_alert(db, alert_id)
    
    # Broadcast update
    import asyncio
    asyncio.create_task(alert_manager.broadcast_alert_update(current_user.id, alert_id, "dismissed"))
    
    return updated_alert


@router.post("/mark-read", response_model=dict)
def mark_multiple_as_read(
    alert_ids: List[int],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Mark multiple alerts as read"""
    # Verify all alerts belong to current user
    for alert_id in alert_ids:
        alert = AlertService.get_alert(db, alert_id)
        if alert and alert.user_id != current_user.id:
            raise HTTPException(status_code=403, detail=f"Not authorized to access alert {alert_id}")
    
    count = AlertService.mark_multiple_as_read(db, alert_ids)
    return {"marked_read": count}
