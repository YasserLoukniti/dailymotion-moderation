import base64
import pytest
import asyncio
import aiomysql
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.database.connection import get_pool, close_pool


def encode_moderator(name: str) -> str:
    """Helper to encode moderator name in base64."""
    return base64.b64encode(name.encode()).decode()


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def db_pool():
    pool = await get_pool()
    yield pool
    await close_pool()


@pytest.fixture(autouse=True)
async def cleanup_db(db_pool):
    yield
    async with db_pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
            await cursor.execute("TRUNCATE TABLE moderation_logs")
            await cursor.execute("TRUNCATE TABLE videos")
            await cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
        await conn.commit()


@pytest.fixture
async def client():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as ac:
        yield ac
