from enum import Enum


class VideoStatus(str, Enum):
    """Video moderation status enum."""
    PENDING = "pending"
    SPAM = "spam"
    NOT_SPAM = "not spam"

    @classmethod
    def is_valid(cls, status: str) -> bool:
        """Check if a status string is valid."""
        return status in [s.value for s in cls]
