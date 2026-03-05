"""
Tests for GET /stats endpoint.

Specs:
- Returns counts of pending, spam, and not spam videos
- Empty queue returns all zeros
- Counts update correctly after flagging
"""
from httpx import AsyncClient

from tests.conftest import add_video, get_video, flag_video


async def test_stats_empty_queue(client: AsyncClient):
    """Empty queue returns all zeros."""
    response = await client.get("/stats")

    assert response.status_code == 200
    data = response.json()
    assert data["total_pending_videos"] == 0
    assert data["total_spam_videos"] == 0
    assert data["total_not_spam_videos"] == 0


async def test_stats_pending_videos(client: AsyncClient):
    """Adding videos increases pending count."""
    await add_video(client, 1)
    await add_video(client, 2)
    await add_video(client, 3)

    response = await client.get("/stats")

    assert response.status_code == 200
    data = response.json()
    assert data["total_pending_videos"] == 3
    assert data["total_spam_videos"] == 0
    assert data["total_not_spam_videos"] == 0


async def test_stats_after_flagging(client: AsyncClient):
    """Counts reflect flagged videos correctly."""
    await add_video(client, 10)
    await add_video(client, 20)
    await add_video(client, 30)

    # Flag video 10 as spam
    await get_video(client, "mod.a")
    await flag_video(client, "mod.a", 10, "spam")

    # Flag video 20 as not spam
    await get_video(client, "mod.b")
    await flag_video(client, "mod.b", 20, "not spam")

    response = await client.get("/stats")

    assert response.status_code == 200
    data = response.json()
    assert data["total_pending_videos"] == 1
    assert data["total_spam_videos"] == 1
    assert data["total_not_spam_videos"] == 1
