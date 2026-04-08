from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from enum import Enum


class AlertTypeEnum(str, Enum):
    """Alert types for Pydantic validation"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    SECURITY = "security"
    DEBUGGER_TOUCH = "debugger_touch"
    CHAIN_BREAK = "chain_break"
    LIE_DETECTED = "lie_detected"
    OVERRIDE_SPOKEN = "override_spoken"
    YUVA9V_TRIPPED = "yuva9v_tripped"
    SYSTEM = "system"


class AlertBase(BaseModel):
    type: AlertTypeEnum
    title: str
    message: str
    source: Optional[str] = None
    severity: str = "medium"
    action_url: Optional[str] = None
    metadata: Optional[str] = None


class AlertCreate(AlertBase):
    user_id: Optional[int] = None


class AlertUpdate(BaseModel):
    is_read: Optional[bool] = None
    is_dismissed: Optional[bool] = None


class AlertInDB(AlertBase):
    id: int
    user_id: Optional[int]
    is_read: bool
    is_dismissed: bool
    created_at: datetime
    read_at: Optional[datetime]
    dismissed_at: Optional[datetime]

    class Config:
        from_attributes = True


class Alert(AlertInDB):
    pass


class AlertList(BaseModel):
    alerts: list[Alert]
    total: int
    unread_count: int


class AlertStats(BaseModel):
    total: int
    unread: int
    by_type: dict[str, int]
    by_severity: dict[str, int]
