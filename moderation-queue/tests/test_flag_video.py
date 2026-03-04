"""
Tests for POST /flag_video endpoint.

Written BEFORE implementation (TDD).

Specs:
- Moderator can flag a video as "spam" or "not spam"
- Video must exist and be pending
- Only the assigned moderator can flag the video
- Returns 200 with video_id and new status on success
- Returns 403 if wrong moderator
- Returns 404 if video not found
- Returns 409 if video already flagged
- Returns 422 if status is invalid
- Returns 401 if Authorization header is missing
"""
import pytest
from httpx import AsyncClient

from tests.conftest import encode_moderator


# ============================================================================
# HELPERS
# ============================================================================

async def add_video(client: AsyncClient, video_id: int) -> None:
    response = await client.post("/add_video", json={"video_id": video_id})
    assert response.status_code == 201


async def get_video(client: AsyncClient, moderator: str):
    return await client.get(
        "/get_video",
        headers={"Authorization": encode_moderator(moderator)}
    )


async def flag_video(client: AsyncClient, moderator: str, video_id: int, status: str):
    return await client.post(
        "/flag_video",
        json={"video_id": video_id, "status": status},
        headers={"Authorization": encode_moderator(moderator)}
    )


# ============================================================================
# TESTS
# ============================================================================

async def test_flag_video_as_spam(client: AsyncClient):
    """Moderator can flag a video as spam."""
    await add_video(client, 111)
    await get_video(client, "john.doe")

    response = await flag_video(client, "john.doe", 111, "spam")

    assert response.status_code == 200
    assert response.json()["video_id"] == 111
    assert response.json()["status"] == "spam"


async def test_flag_video_as_not_spam(client: AsyncClient):
    """Moderator can flag a video as not spam."""
    await add_video(client, 222)
    await get_video(client, "john.doe")

    response = await flag_video(client, "john.doe", 222, "not spam")

    assert response.status_code == 200
    assert response.json()["video_id"] == 222
    assert response.json()["status"] == "not spam"


async def test_flag_video_not_found(client: AsyncClient):
    """Flagging a non-existent video returns 404."""
    response = await flag_video(client, "john.doe", 99999, "spam")

    assert response.status_code == 404


async def test_flag_video_wrong_moderator(client: AsyncClient):
    """Only the assigned moderator can flag the video → 403."""
    await add_video(client, 333)
    await get_video(client, "alice")

    response = await flag_video(client, "bob", 333, "spam")

    assert response.status_code == 403


async def test_flag_video_already_flagged(client: AsyncClient):
    """Flagging an already flagged video returns 409."""
    await add_video(client, 444)
    await get_video(client, "john.doe")
    await flag_video(client, "john.doe", 444, "spam")

    # Try to flag again
    response = await flag_video(client, "john.doe", 444, "not spam")

    assert response.status_code == 409


async def test_flag_video_invalid_status(client: AsyncClient):
    """Invalid status value returns 422."""
    await add_video(client, 555)
    await get_video(client, "john.doe")

    response = await flag_video(client, "john.doe", 555, "invalid_status")

    assert response.status_code == 422


async def test_flag_video_missing_authorization(client: AsyncClient):
    """Missing Authorization header returns 401."""
    await add_video(client, 666)

    response = await client.post(
        "/flag_video",
        json={"video_id": 666, "status": "spam"}
    )

    assert response.status_code == 401


async def test_flag_video_clears_assigned_moderator(client: AsyncClient):
    """After flagging, the video is no longer assigned to the moderator."""
    await add_video(client, 777)
    await get_video(client, "john.doe")
    await flag_video(client, "john.doe", 777, "spam")

    # Moderator should now get a different video (or 204 if queue empty)
    response = await get_video(client, "john.doe")

    assert response.status_code == 204
