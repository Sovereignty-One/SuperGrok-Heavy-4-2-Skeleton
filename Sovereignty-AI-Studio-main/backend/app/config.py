from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    app_name: str = "CreativeFlow AI"
    debug: bool = False

    # Database
    database_url: str = "sqlite:///./sovereignty.db"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Security
    secret_key: str = ""
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # AI Services
    openai_api_key: str = ""

    # CORS
    cors_origins: List[str] = [
        "http://localhost:3000",
        "http://localhost:9898",
        "http://localhost:9000",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:9898",
        "http://127.0.0.1:9000",
    ]

    class Config:
        env_file = ".env"


def _get_settings() -> Settings:
    """Lazy settings loader — generates a secret_key if none is provided."""
    import logging
    s = Settings()
    if not s.secret_key:
        import secrets
        s.secret_key = secrets.token_urlsafe(48)
        logging.getLogger(__name__).warning(
            "SECRET_KEY not set — auto-generated a temporary key. "
            "Set SECRET_KEY in .env for production to preserve sessions across restarts."
        )
    return s


settings = _get_settings()
