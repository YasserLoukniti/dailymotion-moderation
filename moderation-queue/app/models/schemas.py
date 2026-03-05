from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, field_validator

from app.models.enums import VideoStatus


# ============================================================================
# REQUEST MODELS
# ============================================================================

class AddVideoRequest(BaseModel):
    """Request model for adding a video to the moderation queue."""
    video_id: int = Field(..., gt=0, description="Dailymotion video ID")


class FlagVideoRequest(BaseModel):
    """Request model for flagging a video as spam or not spam."""
    video_id: int = Field(..., gt=0, description="Video ID to flag")
    status: str = Field(..., description="New status: 'spam' or 'not spam'")

    @field_validator('status')
    @classmethod
    def validate_status(cls, v: str) -> str:
        """Validate status is spam or not spam only."""
        if v not in [VideoStatus.SPAM.value, VideoStatus.NOT_SPAM.value]:
            raise ValueError(f"Status must be '{VideoStatus.SPAM.value}' or '{VideoStatus.NOT_SPAM.value}'")
        return v


# ============================================================================
# RESPONSE MODELS
# ============================================================================

class VideoResponse(BaseModel):
    """Response model for video data."""
    video_id: int


class FlagVideoResponse(BaseModel):
    """Response model after flagging a video."""
    video_id: int
    status: str


class StatsResponse(BaseModel):
    """Response model for moderation statistics."""
    total_pending_videos: int
    total_spam_videos: int
    total_not_spam_videos: int


class ModerationLogEntry(BaseModel):
    """Single moderation log entry."""
    date: str
    status: str
    moderator: Optional[str]

    @field_validator('date', mode='before')
    @classmethod
    def format_date(cls, v):
        if isinstance(v, datetime):
            return v.strftime("%Y-%m-%d %H:%M:%S")
        return str(v)


class VideoLogsResponse(BaseModel):
    """Response model for video moderation history."""
    logs: List[ModerationLogEntry]


# ============================================================================
# INTERNAL MODELS
# ============================================================================

class Video(BaseModel):
    """Internal video model."""
    id: int
    video_id: int
    status: VideoStatus
    assigned_moderator: Optional[str]
    created_at: datetime
    updated_at: datetime
