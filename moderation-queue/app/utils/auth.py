import base64
import logging
from fastapi import Header, HTTPException, status

logger = logging.getLogger(__name__)


def decode_moderator(authorization: str) -> str:
    """
    Decode the moderator name from a base64-encoded Authorization header.

    Args:
        authorization: Base64-encoded moderator name

    Returns:
        Decoded moderator name

    Raises:
        HTTPException 401: If header is missing or cannot be decoded
    """
    try:
        decoded = base64.b64decode(authorization).decode("utf-8").strip()
        if not decoded:
            raise ValueError("Empty moderator name")
        return decoded
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Authorization header: expected base64-encoded moderator name"
        )


async def get_moderator(authorization: str = Header(default=None)) -> str:
    """
    FastAPI dependency that extracts and decodes the moderator name
    from the Authorization header.

    Usage:
        @router.get("/get_video")
        async def get_video(moderator: str = Depends(get_moderator)):
            ...
    """
    if authorization is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization header"
        )
    return decode_moderator(authorization)
