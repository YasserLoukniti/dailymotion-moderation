"""Custom exceptions for the moderation queue service."""


class VideoNotFoundError(Exception):
    """Raised when a video is not found in the queue."""
    pass


class VideoDuplicateError(Exception):
    """Raised when attempting to add a video that already exists."""
    pass


class VideoAlreadyFlaggedError(Exception):
    """Raised when attempting to flag a video that has already been flagged."""
    pass


class ModeratorNotAssignedError(Exception):
    """Raised when a moderator tries to flag a video not assigned to them."""
    pass
