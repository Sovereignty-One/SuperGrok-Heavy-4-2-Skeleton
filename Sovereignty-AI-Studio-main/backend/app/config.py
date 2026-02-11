from pydantic_settings import BaseSettings
from pydantic import Field, field_validator
from typing import List
import secrets


class Settings(BaseSettings):
    app_name: str = "CreativeFlow AI"
    debug: bool = False

    # Database
    database_url: str = "postgresql://localhost/sovereignty_db"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Security
    secret_key: str = Field(
        default_factory=lambda: secrets.token_urlsafe(32),
        min_length=32,
        description="Secret key for JWT signing - must be at least 32 characters"
    )
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    # AI Services (optional in .env)
    openai_api_key: str = ""

    # CORS
    cors_origins: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:98765"],
        description="Allowed CORS origins"
    )
    
    # Rate Limiting
    rate_limit_enabled: bool = True
    rate_limit_requests: int = 100  # requests per window
    rate_limit_window: int = 60  # window in seconds
    
    # Request Limits
    max_request_size: int = 10 * 1024 * 1024  # 10MB
    
    @field_validator('secret_key')
    @classmethod
    def validate_secret_key(cls, v: str) -> str:
        """Validate secret key meets minimum security requirements."""
        if len(v) < 32:
            raise ValueError('Secret key must be at least 32 characters long')
        # Warn if secret key appears to be weak
        if v.lower() in ['your-secret-key-here', 'changeme', 'secret', 'password']:
            raise ValueError('Secret key is too weak - use a strong random key')
        return v
    
    @field_validator('cors_origins', mode='before')
    @classmethod
    def parse_cors_origins(cls, v):
        """Parse CORS origins from string or list."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(',')]
        return v

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
