from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
import enum


class AlertType(enum.Enum):
    """Alert types based on security events"""
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


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    
    # Alert details
    type = Column(Enum(AlertType), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    
    # Status
    is_read = Column(Boolean, default=False, index=True)
    is_dismissed = Column(Boolean, default=False)
    
    # Additional metadata
    source = Column(String(100), nullable=True)  # Source component/module
    severity = Column(String(20), default="medium")  # low, medium, high, critical
    action_url = Column(String(500), nullable=True)  # Optional link to related resource
    metadata = Column(Text, nullable=True)  # JSON string for additional data
    
    # Timestamps
    created_at = Column(DateTime, default=func.now(), index=True)
    read_at = Column(DateTime, nullable=True)
    dismissed_at = Column(DateTime, nullable=True)

    # Relationships
    user = relationship("User", back_populates="alerts")
