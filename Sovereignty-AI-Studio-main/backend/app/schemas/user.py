from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional
from datetime import datetime
import re
import bleach


def sanitize_html(text: Optional[str]) -> Optional[str]:
    """
    Sanitize HTML content to prevent XSS attacks.
    
    Uses bleach library for proper HTML sanitization.
    Allows only safe tags and attributes.
    
    Args:
        text: Text to sanitize
        
    Returns:
        Sanitized text or None if input was None
    """
    if text is None:
        return text
    
    # Allow only safe tags (none for plain text fields like bio)
    allowed_tags = []
    allowed_attributes = {}
    
    # Strip all HTML tags and sanitize
    sanitized = bleach.clean(
        text,
        tags=allowed_tags,
        attributes=allowed_attributes,
        strip=True
    )
    
    return sanitized.strip()


def validate_url_scheme(url: Optional[str]) -> Optional[str]:
    """
    Validate URL scheme to prevent javascript: and data: URLs.
    
    Args:
        url: URL to validate
        
    Returns:
        Validated URL
        
    Raises:
        ValueError: If URL has invalid scheme
    """
    if url is None:
        return url
    
    # Basic URL validation
    if not url.startswith(('http://', 'https://')):
        raise ValueError('URL must start with http:// or https://')
    
    # Prevent javascript: and data: URLs (case-insensitive)
    if url.lower().startswith(('javascript:', 'data:')):
        raise ValueError('Invalid URL scheme')
    
    return url


class UserBase(BaseModel):
    email: EmailStr
    username: str = Field(
        ...,
        min_length=3,
        max_length=20,
        pattern=r"^[a-zA-Z0-9_-]+$",
        description="Username must be 3-20 characters and contain only letters, numbers, hyphens, and underscores"
    )
    full_name: Optional[str] = Field(None, max_length=100)
    bio: Optional[str] = Field(None, max_length=500)
    avatar_url: Optional[str] = Field(None, max_length=500)
    
    @field_validator('bio')
    @classmethod
    def sanitize_bio(cls, v: Optional[str]) -> Optional[str]:
        """Sanitize bio field using proper HTML sanitization."""
        return sanitize_html(v)
    
    @field_validator('avatar_url')
    @classmethod
    def validate_avatar_url(cls, v: Optional[str]) -> Optional[str]:
        """Validate avatar URL format."""
        return validate_url_scheme(v)


class UserCreate(UserBase):
    password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="Password must be at least 8 characters long"
    )
    
    @field_validator('password')
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """
        Validate password meets security requirements:
        - At least 8 characters
        - At least one uppercase letter
        - At least one lowercase letter
        - At least one digit
        - At least one special character
        """
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one digit')
        
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError('Password must contain at least one special character')
        
        return v


class UserUpdate(BaseModel):
    full_name: Optional[str] = Field(None, max_length=100)
    bio: Optional[str] = Field(None, max_length=500)
    avatar_url: Optional[str] = Field(None, max_length=500)
    
    @field_validator('bio')
    @classmethod
    def sanitize_bio(cls, v: Optional[str]) -> Optional[str]:
        """Sanitize bio field using proper HTML sanitization."""
        return sanitize_html(v)
    
    @field_validator('avatar_url')
    @classmethod
    def validate_avatar_url(cls, v: Optional[str]) -> Optional[str]:
        """Validate avatar URL format."""
        return validate_url_scheme(v)


class UserInDB(UserBase):
    id: int
    is_active: bool
    is_verified: bool
    subscription_plan: str
    subscription_expires_at: Optional[datetime]
    total_generations: int
    monthly_generations: int
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime]

    class Config:
        from_attributes = True


class User(UserInDB):
    pass


class UserLogin(BaseModel):
    username: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None
