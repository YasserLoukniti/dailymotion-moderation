import base64
import pytest
import asyncio
import aiomysql
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.database.connection import get_pool, close_pool
import app.database.connection as connection_module
from app.config import settings
from app.routes.moderation import moderation_service


def encode_moderator(name: str) -> str:
    """Helper to encode moderator name in base64."""
    return base64.b64encode(name.encode()).decode()


@pytest.fixture(autouse=True)
async def cleanup_db():
    # Reset global pool so it's created on this test's event loop
    connection_module._pool = None
    moderation_service.repository.pool = None
    yield
    # Cleanup after test
    pool = await get_pool()
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
            await cursor.execute("DELETE FROM moderation_logs")
            await cursor.execute("DELETE FROM videos")
            await cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
        await conn.commit()
    # Close pool so next test gets a fresh one on its own loop
    pool.close()
    await pool.wait_closed()
    connection_module._pool = None
    moderation_service.repository.pool = None


@pytest.fixture
async def client():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as ac:
        yield ac
