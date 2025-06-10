import logging
from typing import Optional, Dict, Any, List

from app.repositories.video_repository import VideoRepository
from app.models.schemas import (
    VideoResponse,
    FlagVideoResponse,
    StatsResponse,
    ModerationLogEntry,
    VideoLogsResponse
)
from app.models.enums import VideoStatus

logger = logging.getLogger(__name__)


class ModerationService:
    """
    Business logic layer for moderation operations.
    Orchestrates repository calls and enforces business rules.
    """

    def __init__(self):
        self.repository = VideoRepository()

    async def add_video(self, video_id: int) -> VideoResponse:
        """
        Add a video to the moderation queue.

        Args:
            video_id: The video ID to add

        Returns:
            VideoResponse

        Raises:
            ValueError: If video already exists (duplicate)
        """
        # Check if video already exists
        exists = await self.repository.check_video_exists(video_id)
        if exists:
            logger.warning(f"Attempted to add duplicate video {video_id}")
            raise ValueError(f"Video {video_id} already exists in the queue")

        # Add video
        await self.repository.add_video(video_id)

        return VideoResponse(video_id=video_id)

    async def get_video_for_moderator(self, moderator: str) -> Optional[VideoResponse]:
        """
        Get a video for a moderator to review.

        Business rules:
        1. If moderator already has an assigned pending video, return that (idempotent)
        2. Otherwise, assign the oldest pending video to this moderator
        3. If no videos available, return None

        Args:
            moderator: The moderator requesting a video

        Returns:
            VideoResponse with video_id, or None if queue is empty
        """
        # Check if moderator already has an assigned video
        video_id = await self.repository.get_moderator_assigned_video(moderator)

        if video_id is not None:
            logger.info(f"Returning already assigned video {video_id} to {moderator}")
            return VideoResponse(video_id=video_id)

        # Assign next available video
        video_id = await self.repository.assign_next_video(moderator)

        if video_id is None:
            logger.info(f"No videos available for moderator {moderator}")
            return None

        return VideoResponse(video_id=video_id)

    async def flag_video(
        self,
        video_id: int,
        status: str,
        moderator: str
    ) -> FlagVideoResponse:
        """
        Flag a video as spam or not spam.

        Business rules:
        1. Video must exist and be in 'pending' status
        2. Moderator must be the one assigned to this video
        3. Status must be 'spam' or 'not spam'

        Args:
            video_id: The video ID to flag
            status: 'spam' or 'not spam'
            moderator: The moderator flagging the video

        Returns:
            FlagVideoResponse

        Raises:
            ValueError: If video not found or business rules violated
            PermissionError: If moderator is not assigned to this video
        """
        # Get video
        video = await self.repository.get_video_by_id(video_id)

        if video is None:
            raise ValueError(f"Video {video_id} not found")

        # Check if video is pending
        if video['status'] != VideoStatus.PENDING.value:
            raise ValueError(
                f"Video {video_id} has already been flagged as '{video['status']}'"
            )

        # Check if moderator is assigned to this video
        if video['assigned_moderator'] != moderator:
            raise PermissionError(
                f"Video {video_id} is not assigned to moderator {moderator}"
            )

        # Update status
        result = await self.repository.update_video_status(
            video_id,
            status,
            moderator
        )

        return FlagVideoResponse(
            video_id=result['video_id'],
            status=result['status']
        )

    async def get_stats(self) -> StatsResponse:
        """
        Get moderation statistics.

        Returns:
            StatsResponse with counts
        """
        stats = await self.repository.get_stats()
        return StatsResponse(**stats)

    async def get_video_logs(self, video_id: int) -> VideoLogsResponse:
        """
        Get moderation history for a video.

        Args:
            video_id: The video ID

        Returns:
            VideoLogsResponse with log entries

        Raises:
            ValueError: If video not found
        """
        # Check if video exists
        exists = await self.repository.check_video_exists(video_id)
        if not exists:
            raise ValueError(f"Video {video_id} not found")

        # Get logs
        logs_data = await self.repository.get_video_logs(video_id)

        logs = [
            ModerationLogEntry(
                date=log['date'],
                status=log['status'],
                moderator=log['moderator']
            )
            for log in logs_data
        ]

        return VideoLogsResponse(logs=logs)
