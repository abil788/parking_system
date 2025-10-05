import redis
import json
from typing import Optional, Any
from datetime import datetime
from .config import get_settings

settings = get_settings()

# Redis connection pool
redis_client = redis.Redis(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    db=settings.REDIS_DB,
    password=settings.REDIS_PASSWORD if settings.REDIS_PASSWORD else None,
    decode_responses=True,
    socket_connect_timeout=5,
    socket_timeout=5,
    retry_on_timeout=True
)


def get_cache(key: str) -> Optional[Any]:
    """Get value from cache"""
    try:
        value = redis_client.get(key)
        if value:
            return json.loads(value)
        return None
    except Exception as e:
        print(f"Cache get error: {e}")
        return None


def set_cache(key: str, value: Any, ttl: int = None) -> bool:
    """Set value in cache with TTL"""
    try:
        if ttl is None:
            ttl = settings.CACHE_TTL
        
        serialized = json.dumps(value, default=str)
        redis_client.setex(key, ttl, serialized)
        return True
    except Exception as e:
        print(f"Cache set error: {e}")
        return False


def delete_cache(key: str) -> bool:
    """Delete key from cache"""
    try:
        redis_client.delete(key)
        return True
    except Exception as e:
        print(f"Cache delete error: {e}")
        return False


def delete_pattern(pattern: str) -> int:
    """Delete all keys matching pattern"""
    try:
        keys = redis_client.keys(pattern)
        if keys:
            return redis_client.delete(*keys)
        return 0
    except Exception as e:
        print(f"Cache delete pattern error: {e}")
        return 0


def ping() -> bool:
    """Check Redis connection"""
    try:
        return redis_client.ping()
    except:
        return False