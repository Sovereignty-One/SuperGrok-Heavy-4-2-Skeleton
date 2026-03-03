from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    DateTime,
    ForeignKey,
    JSON,
    Boolean,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)

    # Project type: story, social_campaign, presentation, podcast, writing
    project_type = Column(String, nullable=False, index=True)

    # Project status: draft, generating, completed, failed
    status = Column(String, default="draft", index=True)

    # Project settings and metadata
    settings = Column(JSON, nullable=True)
    project_metadata = Column(JSON, nullable=True)

    # Main content (story text, script, etc.)
    content = Column(Text, nullable=True)

    # Sharing and collaboration
    is_public = Column(Boolean, default=False)
    is_featured = Column(Boolean, default=False)
    share_token = Column(String, unique=True, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    completed_at = Column(DateTime, nullable=True)

    # Foreign keys
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Relationships
    owner = relationship("User", back_populates="projects")
    generations = relationship(
        "Generation",
        back_populates="project",
        cascade="all, delete-orphan",
    )
    media_files = relationship(
        "Media",
        back_populates="project",
        cascade="all, delete-orphan",
    )
