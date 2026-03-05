import aiomysql
from typing import Optional
import logging

from app.config import settings

logger = logging.getLogger(__name__)

# Global connection pool
_pool: Optional[aiomysql.Pool] = None


async def get_pool() -> aiomysql.Pool:
    """
    Get or create the aiomysql connection pool.

    Returns:
        aiomysql.Pool: Database connection pool
    """
    global _pool

    if _pool is None:
        logger.info("Creating database connection pool")
        _pool = await aiomysql.create_pool(
            host=settings.database_host,
            port=settings.database_port,
            user=settings.database_user,
            password=settings.database_password,
            db=settings.database_name,
            minsize=settings.db_min_pool_size,
            maxsize=settings.db_max_pool_size,
            autocommit=True,
            charset='utf8mb4',
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
        _pool.close()
        await _pool.wait_closed()
        _pool = None
        logger.info("Connection pool closed")
