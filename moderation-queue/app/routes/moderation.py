import logging
from typing import List

from fastapi import APIRouter, HTTPException, Response, status, Depends

from app.models.schemas import AddVideoRequest, VideoResponse, FlagVideoRequest, FlagVideoResponse, StatsResponse, ModerationLogEntry
from app.services.moderation_service import ModerationService
from app.utils.auth import get_moderator
from app.exceptions import (
    VideoNotFoundError,
    VideoDuplicateError,
    VideoAlreadyFlaggedError,
    ModeratorNotAssignedError,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="", tags=["moderation"])

# Service instance
moderation_service = ModerationService()


@router.post(
    "/add_video",
    status_code=status.HTTP_201_CREATED,
    response_model=None,
    summary="Add a video to the moderation queue"
)
async def add_video(request: AddVideoRequest):
    """
    Add a video to the moderation queue.

    - **video_id**: Dailymotion video ID (positive integer)

    Returns HTTP 201 on success.
    Returns HTTP 409 if video already exists.
    Returns HTTP 422 if validation fails.
    """
    try:
        await moderation_service.add_video(request.video_id)
        return None  # 201 with no body
    except VideoDuplicateError as e:
        logger.warning(f"Duplicate video: {e}")
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except Exception as e:
        logger.error(f"Error adding video: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get(
    "/get_video",
    response_model=VideoResponse,
    responses={204: {"description": "No pending videos in queue"}},
    summary="Get next pending video for moderation"
)
async def get_video(moderator: str = Depends(get_moderator)):
    """
    Get the next pending video for a moderator.

    - Same moderator always gets the same video (idempotent)
    - Different moderators get different videos (FIFO, concurrent-safe)
    - Uses SELECT FOR UPDATE SKIP LOCKED to prevent race conditions

    Returns HTTP 200 with video_id on success.
    Returns HTTP 204 if queue is empty.
    Returns HTTP 401 if Authorization header is missing or invalid.
    """
    try:
        result = await moderation_service.get_video_for_moderator(moderator)

        if result is None:
            return Response(status_code=status.HTTP_204_NO_CONTENT)

        return result
    except Exception as e:
        logger.error(f"Error getting video for moderator {moderator}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.post(
    "/flag_video",
    response_model=FlagVideoResponse,
    summary="Flag a video as spam or not spam"
)
async def flag_video(
    request: FlagVideoRequest,
    moderator: str = Depends(get_moderator)
):
    """
    Flag a video as spam or not spam.

    Returns HTTP 200 with video_id and new status.
    Returns HTTP 403 if moderator is not assigned to this video.
    Returns HTTP 404 if video not found.
    Returns HTTP 409 if video already flagged.
    Returns HTTP 422 if status is invalid.
    """
    try:
        result = await moderation_service.flag_video(
            request.video_id,
            request.status,
            moderator
        )
        return result
    except VideoNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ModeratorNotAssignedError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except VideoAlreadyFlaggedError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except Exception as e:
        logger.error(f"Error flagging video: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get(
    "/stats",
    response_model=StatsResponse,
    summary="Get moderation queue statistics"
)
async def stats():
    """
    Get the number of videos by status.

    Returns HTTP 200 with counts for pending, spam, and not spam videos.
    """
    try:
        return await moderation_service.get_stats()
    except Exception as e:
        logger.error(f"Error getting stats: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get(
    "/log_video/{video_id}",
    response_model=List[ModerationLogEntry],
    summary="Get moderation history for a video"
)
async def log_video(video_id: int):
    """
    Get the moderation history of a video for audit purposes.

    Returns HTTP 200 with a list of log entries.
    Returns HTTP 404 if video not found.
    """
    try:
        result = await moderation_service.get_video_logs(video_id)
        return result.logs
    except VideoNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting logs for video {video_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )
