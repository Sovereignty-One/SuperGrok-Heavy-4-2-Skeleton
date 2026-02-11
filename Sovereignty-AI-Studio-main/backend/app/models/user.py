from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String, nullable=True)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    avatar_url = Column(String, nullable=True)
    bio = Column(Text, nullable=True)

    # Subscription/Plan info
    subscription_plan = Column(String, default="free")  # free, pro, enterprise
    subscription_expires_at = Column(DateTime, nullable=True)

    # Usage tracking
    total_generations = Column(Integer, default=0)
    monthly_generations = Column(Integer, default=0)
    last_generation_reset = Column(DateTime, default=func.now())

    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    last_login = Column(DateTime, nullable=True)

    # Relationships
    projects = relationship(
        "Project",
        back_populates="owner",
        cascade="all, delete-orphan",
    )
    generations = relationship(
        "Generation",
        back_populates="user",
        cascade="all, delete-orphan",
    )
