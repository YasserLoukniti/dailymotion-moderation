import logging
from typing import Optional

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

FIELDS = "title,channel,owner,filmstrip_60_url,embed_url"


async def fetch_video_info() -> dict:
    """
    Fetch video info from Dailymotion API.

    As per test spec, always fetches the reference video (x2m8jpp)
    regardless of the requested video_id.

    Raises:
        httpx.TimeoutException: on timeout
        httpx.HTTPStatusError: on API error
    """
    url = f"{settings.dailymotion_api_base_url}/video/{settings.reference_video_id}"
    params = {"fields": FIELDS}

    async with httpx.AsyncClient(timeout=settings.http_timeout) as client:
        response = await client.get(url, params=params)
        response.raise_for_status()
        return response.json()
