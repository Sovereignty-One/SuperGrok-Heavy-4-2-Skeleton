from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    DateTime,
    ForeignKey,
    JSON,
    Float,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class Generation(Base):
    __tablename__ = "generations"

    id = Column(Integer, primary_key=True, index=True)

    # Generation type: text, image, audio, video
    generation_type = Column(String, nullable=False, index=True)

    # AI service used: openai, elevenlabs, stability, etc.
    ai_service = Column(String, nullable=False)

    # Generation status: pending, processing, completed, failed
    status = Column(String, default="pending", index=True)

    # Input and output
    prompt = Column(Text, nullable=False)  # User's input prompt
    # Generated content (text or file reference)
    result = Column(Text, nullable=True)

    # Request parameters
    parameters = Column(JSON, nullable=True)  # AI service parameters

    # Processing info
    processing_time = Column(Float, nullable=True)  # Time taken in seconds
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0)

    # Cost tracking
    tokens_used = Column(Integer, nullable=True)
    cost_usd = Column(Float, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=func.now())
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    # Foreign keys
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)

    # Relationships
    user = relationship("User", back_populates="generations")
    project = relationship("Project", back_populates="generations")
    media_files = relationship(
        "Media",
        back_populates="generation",
        cascade="all, delete-orphan",
    )
