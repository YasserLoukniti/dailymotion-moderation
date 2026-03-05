import logging

import httpx
from fastapi import APIRouter, HTTPException, status

from app.models.schemas import VideoInfoResponse
from app.services import cache_service, dailymotion_client

logger = logging.getLogger(__name__)

router = APIRouter(tags=["proxy"])


@router.get(
    "/get_video_info/{video_id}",
    response_model=VideoInfoResponse,
    summary="Get video information from Dailymotion API"
)
async def get_video_info(video_id: int):
    """
    Proxy to Dailymotion API with Redis caching.

    - video_id ending with 404 returns HTTP 404
    - Cache hit returns cached data
    - Cache miss fetches from Dailymotion API, caches, and returns

    Returns HTTP 200 with video info.
    Returns HTTP 404 if video_id ends with 404.
    Returns HTTP 502 on Dailymotion API error.
    Returns HTTP 504 on Dailymotion API timeout.
    """
    # Check the 404 rule
    if str(video_id).endswith("404"):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Video {video_id} not found"
        )

    cache_key = f"video_info:{video_id}"

    # Try cache first
    cached = await cache_service.cache_get(cache_key)
    if cached is not None:
        return cached

    # Fetch from Dailymotion API
    try:
        data = await dailymotion_client.fetch_video_info()
    except httpx.TimeoutException:
        logger.error(f"Timeout fetching video info for {video_id}")
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Dailymotion API timeout"
        )
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 429:
            retry_after = e.response.headers.get("Retry-After", "60")
            logger.warning(f"Rate limited by Dailymotion API")
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Dailymotion API rate limit exceeded",
                headers={"Retry-After": retry_after}
            )
        logger.error(f"Dailymotion API error: {e.response.status_code}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Dailymotion API error: {e.response.status_code}"
        )
    except Exception as e:
        logger.error(f"Unexpected error fetching video info: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to fetch video info"
        )

    # Cache the result
    await cache_service.cache_set(cache_key, data)

    return data
