"""
Tests for POST /add_video endpoint.

Specs:
- Adds a new video to the moderation queue
- Returns 201 on success
- Returns 409 if video already exists
- Returns 422 if video_id is invalid (zero, negative)
"""
from httpx import AsyncClient

from tests.conftest import add_video


async def test_add_video_success(client: AsyncClient):
    """Adding a new video returns 201."""
    response = await client.post("/add_video", json={"video_id": 1})

    assert response.status_code == 201
    assert response.json()["video_id"] == 1


async def test_add_video_duplicate(client: AsyncClient):
    """Adding the same video twice returns 409."""
    await add_video(client, 500)

    response = await client.post("/add_video", json={"video_id": 500})

    assert response.status_code == 409


async def test_add_video_invalid_id(client: AsyncClient):
    """Invalid video_id (zero or negative) returns 422."""
    response = await client.post("/add_video", json={"video_id": 0})
    assert response.status_code == 422

    response = await client.post("/add_video", json={"video_id": -1})
    assert response.status_code == 422
