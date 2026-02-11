# app/core/redis.py
import redis
from app.config import settings

# Lazy-initialized global client — safe for FastAPI lifespan
_redis_client = None


def get_redis() -> redis.Redis:
    """Dependency to inject Redis client."""
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.from_url(
            settings.redis_url,
            decode_responses=True,
            socket_connect_timeout=5,
            socket_timeout=5,
            retry_on_timeout=True,
        )
    return _redis_client
