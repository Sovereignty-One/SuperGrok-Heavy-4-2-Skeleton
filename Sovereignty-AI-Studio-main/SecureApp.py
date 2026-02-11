"""secure_app_module.py

Unified secure module combining:
1. User Authentication (JWT + Password Hashing)
2. Redis Cache Connection
3. SQLAlchemy Media Model for file storage

Author: Midas Touch Enhanced
License: MIT
"""

from datetime import datetime, timedelta
from typing import Optional, Dict
import redis
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import (
    Column, Integer, String, Text, DateTime, ForeignKey, Boolean, BigInteger
)
from sqlalchemy.sql import func
from app.config import settings
from app.core.database import Base

# ============================================================
# 1. SECURITY: JWT + PASSWORD HASHING
# ============================================================
"""This section handles:
- Password hashing using bcrypt
- JWT token creation and validation for authentication."""

pwd_context: CryptContext = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_access_token(data: Dict[str, str], expires_delta: Optional[timedelta] = None) -> str:
    # Create a signed JWT access token for a given payload
    to_encode: Dict[str, str] = data.copy()
    expire: datetime = datetime.utcnow() + (expires_delta or timedelta(
        minutes=settings.access_token_expire_minutes
    ))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    # Verify a plain password against its hashed counterpart
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    # Generate a bcrypt hash for the given password
    return pwd_context.hash(password)

def verify_token(token: str) -> Optional[str]:
    # Decode and validate a JWT token, returning username if valid
    try:
        payload: Dict[str, str] = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        return payload.get("sub")
    except JWTError:
        return None

# Example usage:
# user_data = {"sub": "alice"}
# token = create_access_token(user_data)
# print("JWT Token:", token)
# print("Verified username:", verify_token(token))

# ============================================================
# 2. REDIS CACHE CONNECTION
# ============================================================
"""This section initializes and provides access to a singleton Redis client.

Note: decode_responses=True is safe only if you do not store binary data.
Otherwise, set decode_responses=False and decode manually where needed."""

redis_client: redis.Redis = redis.from_url(settings.redis_url, decode_responses=True)

def get_redis() -> redis.Redis:
    # Return the singleton Redis client instance
    return redis_client

# Example usage:
# r = get_redis()
# r.set("key", "value")
# print("Redis stored value:", r.get("key"))

# ============================================================
# 3. MEDIA ORM MODEL (SQLAlchemy)
# ============================================================
"""This section defines the Media model.

The Media class represents a file stored in local or cloud storage, including
metadata, processing status, and links to projects or generations."""

class Media(Base):
    __tablename__ = "media"

    id: int = Column(Integer, primary_key=True, index=True)
    filename: str = Column(String, nullable=False)
    original_filename: Optional[str] = Column(String, nullable=True)
    file_path: str = Column(String, nullable=False)
    file_url: Optional[str] = Column(String, nullable=True)
    file_type: str = Column(String, nullable=False)
    mime_type: str = Column(String, nullable=False)
    file_size: int = Column(BigInteger, nullable=False)
    width: Optional[int] = Column(Integer, nullable=True)
    height: Optional[int] = Column(Integer, nullable=True)
    duration: Optional[int] = Column(Integer, nullable=True)
    is_processed: bool = Column(Boolean, default=False)
    processing_status: str = Column(String, default="pending")
    title: Optional[str] = Column(String, nullable=True)
    description: Optional[str] = Column(Text, nullable=True)
    alt_text: Optional[str] = Column(String, nullable=True)
    storage_provider: str = Column(String, default="local")
    storage_bucket: Optional[str] = Column(String, nullable=True)
    storage_key: Optional[str] = Column(String, nullable=True)
    created_at: datetime = Column(DateTime, default=func.now())
    updated_at: datetime = Column(DateTime, default=func.now(), onupdate=func.now())
    project_id: Optional[int] = Column(Integer, ForeignKey("projects.id"), nullable=True)
    generation_id: Optional[int] = Column(Integer, ForeignKey("generations.id"), nullable=True)

    def __repr__(self) -> str:
        # Return a concise string representation for logging
        return (
            f"<Media id={self.id} filename={self.filename!r} "
            f"file_type={self.file_type!r} size={self.file_size}B "
            f"status={self.processing_status!r}>"
        )

# Example usage:
# media_item = Media(
#     filename="example.png",
#     file_path="/uploads/example.png",
#     file_type="image",
#     mime_type="image/png",
#     file_size=1024
# )
# print(media_item)
Secure App Module – Landscape Wall Poster (Condensed)

---

User Authentication
	⁃	Hash Password: get_password_hash("password")
	⁃	Verify Password: verify_password("password", hashed_pw)
	⁃	Create JWT: create_access_token({"sub": "username"})
	⁃	Verify JWT: verify_token(token)

---

Redis Cache
	⁃	Get Client: r = get_redis()
	⁃	Set Value: r.set("key", "value")
	⁃	Get Value: r.get("key")

---

Media ORM Model
	⁃	Create Record:
Media(filename="example.png", file_path="/uploads/example.png", file_type="image", mime_type="image/png", file_size=1024)
	⁃	Print Record: print(media_item)

Attributes: filename • filepath • filetype • mimetype • filesize • width • height • duration • storage_key

---

Author: Midas Touch Enhanced | License: MIT
