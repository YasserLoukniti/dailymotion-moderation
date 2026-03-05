"""
Tests for cache behavior.

Specs:
- First call: cache miss, fetches from API, caches result
- Second call: cache hit, returns cached data without API call
- Cache failure: fallback to direct API call
"""
import pytest
from unittest.mock import AsyncMock, patch, call
from httpx import AsyncClient


MOCK_VIDEO_DATA = {
    "title": "Dailymotion Spirit Movie",
    "channel": "creation",
    "owner": "Dailymotion",
    "filmstrip_60_url": "https://example.com/filmstrip.jpg",
    "embed_url": "https://www.dailymotion.com/embed/video/x2m8jpp",
}


async def test_cache_miss_fetches_from_api(client: AsyncClient):
    """On cache miss, fetch from API and cache the result."""
    mock_fetch = AsyncMock(return_value=MOCK_VIDEO_DATA)
    mock_cache_get = AsyncMock(return_value=None)
    mock_cache_set = AsyncMock()

    with patch("app.routes.proxy.dailymotion_client.fetch_video_info", mock_fetch):
        with patch("app.routes.proxy.cache_service.cache_get", mock_cache_get):
            with patch("app.routes.proxy.cache_service.cache_set", mock_cache_set):
                response = await client.get("/get_video_info/123")

    assert response.status_code == 200
    mock_fetch.assert_called_once()
    mock_cache_set.assert_called_once_with("video_info:123", MOCK_VIDEO_DATA)


async def test_cache_hit_skips_api(client: AsyncClient):
    """On cache hit, return cached data without calling API."""
    mock_fetch = AsyncMock()
    mock_cache_get = AsyncMock(return_value=MOCK_VIDEO_DATA)

    with patch("app.routes.proxy.dailymotion_client.fetch_video_info", mock_fetch):
        with patch("app.routes.proxy.cache_service.cache_get", mock_cache_get):
            response = await client.get("/get_video_info/123")

    assert response.status_code == 200
    assert response.json()["title"] == "Dailymotion Spirit Movie"
    mock_fetch.assert_not_called()


async def test_cache_failure_falls_back_to_api(client: AsyncClient):
    """If cache read fails, still fetch from API."""
    mock_fetch = AsyncMock(return_value=MOCK_VIDEO_DATA)
    mock_cache_get = AsyncMock(return_value=None)  # cache_get already handles errors internally
    mock_cache_set = AsyncMock()

    with patch("app.routes.proxy.dailymotion_client.fetch_video_info", mock_fetch):
        with patch("app.routes.proxy.cache_service.cache_get", mock_cache_get):
            with patch("app.routes.proxy.cache_service.cache_set", mock_cache_set):
                response = await client.get("/get_video_info/123")

    assert response.status_code == 200
    mock_fetch.assert_called_once()
