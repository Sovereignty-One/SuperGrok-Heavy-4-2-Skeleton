# app/core/redis.py
import redis
from app.config import settings

# Single global client — safe for FastAPI lifespan
redis_client = redis.from_url(
    settings.redis_url,
    decode_responses=True,
    socket_connect_timeout=5,
    socket_timeout=5,
    retry_on_timeout=True,
)

def get_redis() -> redis.Redis:
    """Dependency to inject Redis client."""
    return redis_client
