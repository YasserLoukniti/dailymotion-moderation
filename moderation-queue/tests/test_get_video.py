"""
Tests for GET /get_video endpoint.

Written BEFORE implementation (TDD).

Specs:
- Moderator gets the oldest pending video (FIFO)
- Same moderator always gets the same pending video (idempotent)
- Different moderators get different videos
- Returns 204 if queue is empty
- Returns 401 if Authorization header is missing or invalid
- Concurrent moderators must NEVER get the same video
"""
import asyncio
from httpx import AsyncClient

from tests.conftest import add_video, get_video

async def test_get_video_returns_200_with_video_id(client: AsyncClient):
    """Basic case: moderator gets a pending video."""
    await add_video(client, 111)

    response = await get_video(client, "john.doe")

    assert response.status_code == 200
    assert response.json()["video_id"] == 111


async def test_get_video_returns_204_when_queue_empty(client: AsyncClient):
    """No pending videos → 204 No Content."""
    response = await get_video(client, "john.doe")

    assert response.status_code == 204


async def test_get_video_fifo_order(client: AsyncClient):
    """Videos must be returned in FIFO order (oldest first)."""
    await add_video(client, 101)
    await add_video(client, 102)
    await add_video(client, 103)

    r1 = await get_video(client, "moderator.a")
    r2 = await get_video(client, "moderator.b")
    r3 = await get_video(client, "moderator.c")

    assert r1.json()["video_id"] == 101
    assert r2.json()["video_id"] == 102
    assert r3.json()["video_id"] == 103


async def test_get_video_idempotent_same_moderator(client: AsyncClient):
    """Same moderator calling get_video twice gets the same video."""
    await add_video(client, 200)
    await add_video(client, 201)

    r1 = await get_video(client, "john.doe")
    r2 = await get_video(client, "john.doe")

    assert r1.status_code == 200
    assert r2.status_code == 200
    assert r1.json()["video_id"] == r2.json()["video_id"]


async def test_get_video_different_moderators_get_different_videos(client: AsyncClient):
    """Two moderators must never get the same video."""
    await add_video(client, 301)
    await add_video(client, 302)

    r1 = await get_video(client, "alice")
    r2 = await get_video(client, "bob")

    assert r1.status_code == 200
    assert r2.status_code == 200
    assert r1.json()["video_id"] != r2.json()["video_id"]


async def test_get_video_missing_authorization_header(client: AsyncClient):
    """Missing Authorization header → 401."""
    response = await client.get("/get_video")

    assert response.status_code == 401


async def test_get_video_invalid_base64_authorization(client: AsyncClient):
    """Invalid base64 Authorization header → 401."""
    response = await client.get(
        "/get_video",
        headers={"Authorization": "not-valid-base64!!!"}
    )

    assert response.status_code == 401


async def test_get_video_concurrent_moderators_get_unique_videos(client: AsyncClient):
    """
    CRITICAL: 10 concurrent moderators must all get different videos.

    This test validates that SELECT FOR UPDATE SKIP LOCKED works correctly
    and prevents two moderators from being assigned the same video.
    """
    # Add 10 videos
    for i in range(1, 11):
        await add_video(client, 1000 + i)

    # 10 moderators call get_video simultaneously
    moderators = [f"moderator.{i}" for i in range(10)]
    tasks = [get_video(client, m) for m in moderators]
    responses = await asyncio.gather(*tasks)

    video_ids = [r.json()["video_id"] for r in responses if r.status_code == 200]

    # All must have gotten a video
    assert len(video_ids) == 10

    # All video IDs must be unique — no two moderators got the same video
    assert len(set(video_ids)) == 10
