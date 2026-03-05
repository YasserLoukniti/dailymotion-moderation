from typing import Optional
from pydantic import BaseModel


class VideoInfoResponse(BaseModel):
    """Response model for video info from Dailymotion API."""
    title: str
    channel: str
    owner: str
    filmstrip_60_url: Optional[str] = None
    embed_url: str
