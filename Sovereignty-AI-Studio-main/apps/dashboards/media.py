from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    DateTime,
    ForeignKey,
    Boolean,
    BigInteger,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class Media(Base):
    __tablename__ = "media"

    id = Column(Integer, primary_key=True, index=True)

    # File information
    filename = Column(String, nullable=False)
    original_filename = Column(String, nullable=True)
    # Path in storage (S3, local, etc.)
    file_path = Column(String, nullable=False)
    # Public URL if available
    file_url = Column(String, nullable=True)

    # File metadata
    file_type = Column(String, nullable=False)  # image, audio, video, document
    mime_type = Column(String, nullable=False)
    file_size = Column(BigInteger, nullable=False)  # Size in bytes

    # Media-specific metadata
    width = Column(Integer, nullable=True)  # For images/videos
    height = Column(Integer, nullable=True)  # For images/videos
    duration = Column(Integer, nullable=True)  # For audio/video (seconds)

    # Processing status
    is_processed = Column(Boolean, default=False)
    # pending, processing, completed, failed
    processing_status = Column(String, default="pending")

    # Content description
    title = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    alt_text = Column(String, nullable=True)  # For accessibility

    # Storage information
    storage_provider = Column(String, default="local")  # local, s3, etc.
    storage_bucket = Column(String, nullable=True)
    storage_key = Column(String, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Foreign keys
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)
    generation_id = Column(
        Integer,
        ForeignKey("generations.id"),
        nullable=True,
    )

    # Relationships
    project = relationship("Project", back_populates="media_files")
    generation = relationship("Generation", back_populates="media_files")
