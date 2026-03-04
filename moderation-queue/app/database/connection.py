import asyncpg
from typing import Optional
import logging

from app.config import settings

logger = logging.getLogger(__name__)

# Global connection pool
_pool: Optional[asyncpg.Pool] = None


async def get_pool() -> asyncpg.Pool:
    """
    Get or create the asyncpg connection pool.

    Returns:
        asyncpg.Pool: Database connection pool
    """
    global _pool

    if _pool is None:
        logger.info("Creating database connection pool")
        _pool = await asyncpg.create_pool(
            settings.database_url,
            min_size=settings.db_min_pool_size,
            max_size=settings.db_max_pool_size,
            command_timeout=60,
        )
        logger.info(
            f"Connection pool created (min={settings.db_min_pool_size}, "
            f"max={settings.db_max_pool_size})"
        )

    return _pool


async def close_pool() -> None:
    """Close the database connection pool."""
    global _pool

    if _pool is not None:
        logger.info("Closing database connection pool")
        await _pool.close()
        _pool = None
        logger.info("Connection pool closed")
