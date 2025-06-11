import logging
from fastapi import APIRouter, HTTPException, status, Depends

from app.models.schemas import AddVideoRequest, VideoResponse
from app.services.moderation_service import ModerationService
from app.utils.auth import get_moderator

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
    except ValueError as e:
        # Video already exists
        logger.warning(f"Duplicate video: {e}")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )
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
            # No content — queue is empty
            from fastapi import Response
            return Response(status_code=status.HTTP_204_NO_CONTENT)

        return result
    except Exception as e:
        logger.error(f"Error getting video for moderator {moderator}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )
