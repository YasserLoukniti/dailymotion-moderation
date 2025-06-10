import logging
from fastapi import APIRouter, HTTPException, status
from asyncpg.exceptions import UniqueViolationError

from app.models.schemas import AddVideoRequest, VideoResponse
from app.services.moderation_service import ModerationService

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
