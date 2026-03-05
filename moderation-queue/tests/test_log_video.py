"""
Tests for GET /log_video/{video_id} endpoint.

Specs:
- Returns moderation history as a list of log entries
- Each entry has date, status, and moderator
- Initial entry has status "pending" and moderator null
- After flagging, a second entry appears with moderator name
- Returns 404 if video not found
"""
import pytest
from httpx import AsyncClient

from tests.conftest import encode_moderator


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


async def test_log_video_initial_entry(client: AsyncClient):
    """After adding a video, log has one entry with status pending."""
    await add_video(client, 100)

    response = await client.get("/log_video/100")

    assert response.status_code == 200
    logs = response.json()
    assert len(logs) == 1
    assert logs[0]["status"] == "pending"
    assert logs[0]["moderator"] is None
    assert "date" in logs[0]


async def test_log_video_after_flagging(client: AsyncClient):
    """After flagging, log has two entries in chronological order."""
    await add_video(client, 200)
    await get_video(client, "john.doe")
    await flag_video(client, "john.doe", 200, "spam")

    response = await client.get("/log_video/200")

    assert response.status_code == 200
    logs = response.json()
    assert len(logs) == 2
    # First entry: pending
    assert logs[0]["status"] == "pending"
    assert logs[0]["moderator"] is None
    # Second entry: spam by john.doe
    assert logs[1]["status"] == "spam"
    assert logs[1]["moderator"] == "john.doe"


async def test_log_video_not_found(client: AsyncClient):
    """Requesting logs for a non-existent video returns 404."""
    response = await client.get("/log_video/99999")

    assert response.status_code == 404
