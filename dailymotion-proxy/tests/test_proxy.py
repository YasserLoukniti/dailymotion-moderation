"""
Tests for GET /get_video_info/{video_id} endpoint.

Specs:
- Returns video info with title, channel, owner, filmstrip_60_url, embed_url
- video_id ending with 404 returns HTTP 404
- Dailymotion API timeout returns HTTP 504
- Dailymotion API error returns HTTP 502
- Dailymotion API rate limit returns HTTP 429 with Retry-After header
"""
import pytest
from unittest.mock import AsyncMock, patch
from httpx import AsyncClient

import httpx


MOCK_VIDEO_DATA = {
    "title": "Dailymotion Spirit Movie",
    "channel": "creation",
    "owner": "Dailymotion",
    "filmstrip_60_url": "https://example.com/filmstrip.jpg",
    "embed_url": "https://www.dailymotion.com/embed/video/x2m8jpp",
}


async def test_get_video_info_success(client: AsyncClient):
    """Normal request returns video info."""
    with patch(
        "app.routes.proxy.dailymotion_client.fetch_video_info",
        new_callable=AsyncMock,
        return_value=MOCK_VIDEO_DATA,
    ):
        with patch("app.routes.proxy.cache_service.cache_get", new_callable=AsyncMock, return_value=None):
            with patch("app.routes.proxy.cache_service.cache_set", new_callable=AsyncMock):
                response = await client.get("/get_video_info/123456")

    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Dailymotion Spirit Movie"
    assert data["channel"] == "creation"
    assert data["owner"] == "Dailymotion"
    assert "embed_url" in data


async def test_get_video_info_404_rule(client: AsyncClient):
    """video_id ending with 404 returns HTTP 404."""
    response = await client.get("/get_video_info/123404")
    assert response.status_code == 404

    response = await client.get("/get_video_info/404")
    assert response.status_code == 404

    response = await client.get("/get_video_info/10404")
    assert response.status_code == 404


async def test_get_video_info_timeout(client: AsyncClient):
    """Dailymotion API timeout returns 504."""
    with patch(
        "app.routes.proxy.dailymotion_client.fetch_video_info",
        new_callable=AsyncMock,
        side_effect=httpx.TimeoutException("timeout"),
    ):
        with patch("app.routes.proxy.cache_service.cache_get", new_callable=AsyncMock, return_value=None):
            response = await client.get("/get_video_info/123456")

    assert response.status_code == 504


async def test_get_video_info_api_error(client: AsyncClient):
    """Dailymotion API error returns 502."""
    mock_response = httpx.Response(500, request=httpx.Request("GET", "https://api.dailymotion.com"))
    with patch(
        "app.routes.proxy.dailymotion_client.fetch_video_info",
        new_callable=AsyncMock,
        side_effect=httpx.HTTPStatusError("error", request=mock_response.request, response=mock_response),
    ):
        with patch("app.routes.proxy.cache_service.cache_get", new_callable=AsyncMock, return_value=None):
            response = await client.get("/get_video_info/123456")

    assert response.status_code == 502


async def test_get_video_info_rate_limited(client: AsyncClient):
    """Dailymotion API rate limit returns 429 with Retry-After."""
    mock_response = httpx.Response(
        429,
        request=httpx.Request("GET", "https://api.dailymotion.com"),
        headers={"Retry-After": "120"},
    )
    with patch(
        "app.routes.proxy.dailymotion_client.fetch_video_info",
        new_callable=AsyncMock,
        side_effect=httpx.HTTPStatusError("rate limited", request=mock_response.request, response=mock_response),
    ):
        with patch("app.routes.proxy.cache_service.cache_get", new_callable=AsyncMock, return_value=None):
            response = await client.get("/get_video_info/123456")

    assert response.status_code == 429
    assert response.headers["Retry-After"] == "120"
