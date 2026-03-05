"""
Tests for GET /log_video/{video_id} endpoint.

Specs:
- Returns moderation history as a list of log entries
- Each entry has date, status, and moderator
- Initial entry has status "pending" and moderator null
- After flagging, a second entry appears with moderator name
- Returns 404 if video not found
"""
from httpx import AsyncClient

from tests.conftest import add_video, get_video, flag_video


async def test_log_video_initial_entry(client: AsyncClient):
    """After adding a video, log has one entry with status pending."""
    await add_video(client, 100)

    response = await client.get("/log_video/100")

    assert response.status_code == 200
    logs = response.json()
    assert len(logs) == 1
    assert logs[0]["status"] == "pending"
    assert logs[0]["moderator"] is None
    # Date format must be "YYYY-MM-DD HH:MM:SS" (not ISO with T)
    assert " " in logs[0]["date"]
    assert "T" not in logs[0]["date"]


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


async def test_log_video_chronological_order(client: AsyncClient):
    """Log entries are in chronological order (second date >= first)."""
    await add_video(client, 300)
    await get_video(client, "john.doe")
    await flag_video(client, "john.doe", 300, "not spam")

    response = await client.get("/log_video/300")

    assert response.status_code == 200
    logs = response.json()
    assert len(logs) == 2
    assert logs[0]["date"] <= logs[1]["date"]


async def test_log_video_not_found(client: AsyncClient):
    """Requesting logs for a non-existent video returns 404."""
    response = await client.get("/log_video/99999")

    assert response.status_code == 404
