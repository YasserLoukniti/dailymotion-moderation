import json
import logging
from typing import Optional

import redis.asyncio as redis

from app.config import settings

logger = logging.getLogger(__name__)

_redis_client: Optional[redis.Redis] = None


async def get_redis() -> redis.Redis:
    """Get or create the Redis client."""
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.from_url(settings.redis_url, decode_responses=True)
    return _redis_client


async def close_redis() -> None:
    """Close the Redis connection."""
    global _redis_client
    if _redis_client is not None:
        await _redis_client.close()
        _redis_client = None


async def cache_get(key: str) -> Optional[dict]:
    """Get a value from cache. Returns None on miss or error."""
    try:
        client = await get_redis()
        data = await client.get(key)
        if data is not None:
            logger.info(f"Cache hit: {key}")
            return json.loads(data)
        logger.info(f"Cache miss: {key}")
        return None
    except Exception as e:
        logger.warning(f"Cache read error: {e}")
        return None


async def cache_set(key: str, value: dict, ttl: int = settings.cache_ttl) -> None:
    """Set a value in cache with TTL. Silently fails on error."""
    try:
        client = await get_redis()
        await client.set(key, json.dumps(value), ex=ttl)
        logger.info(f"Cached: {key} (TTL={ttl}s)")
    except Exception as e:
        logger.warning(f"Cache write error: {e}")
