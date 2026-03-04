"""
Raw SQL queries for the moderation system.

All queries are defined as constants to maintain visibility and control
over database operations (no ORM as per requirements).
"""

# ============================================================================
# VIDEO QUERIES
# ============================================================================

INSERT_VIDEO = """
INSERT INTO videos (video_id, status, created_at, updated_at)
VALUES ($1, 'pending', NOW(), NOW())
RETURNING id, video_id, status, assigned_moderator, created_at, updated_at
"""

CHECK_VIDEO_EXISTS = """
SELECT video_id FROM videos WHERE video_id = $1
"""

GET_MODERATOR_ASSIGNED_VIDEO = """
SELECT video_id FROM videos
WHERE assigned_moderator = $1 AND status = 'pending'
LIMIT 1
"""

GET_NEXT_PENDING_VIDEO_FOR_UPDATE = """
SELECT video_id FROM videos
WHERE status = 'pending' AND assigned_moderator IS NULL
ORDER BY created_at ASC
LIMIT 1
FOR UPDATE SKIP LOCKED
"""

ASSIGN_VIDEO_TO_MODERATOR = """
UPDATE videos
SET assigned_moderator = $1, updated_at = NOW()
WHERE video_id = $2
RETURNING video_id
"""

GET_VIDEO_BY_ID = """
SELECT id, video_id, status, assigned_moderator, created_at, updated_at
FROM videos
WHERE video_id = $1
"""

UPDATE_VIDEO_STATUS = """
UPDATE videos
SET status = $1, assigned_moderator = NULL, updated_at = NOW()
WHERE video_id = $2
RETURNING video_id, status
"""

# ============================================================================
# STATS QUERIES
# ============================================================================

GET_STATS = """
SELECT
    COUNT(*) FILTER (WHERE status = 'pending') AS total_pending_videos,
    COUNT(*) FILTER (WHERE status = 'spam') AS total_spam_videos,
    COUNT(*) FILTER (WHERE status = 'not spam') AS total_not_spam_videos
FROM videos
"""

# ============================================================================
# MODERATION LOG QUERIES
# ============================================================================

INSERT_MODERATION_LOG = """
INSERT INTO moderation_logs (video_id, status, moderator, created_at)
VALUES ($1, $2, $3, NOW())
"""

GET_VIDEO_LOGS = """
SELECT created_at AS date, status, moderator
FROM moderation_logs
WHERE video_id = $1
ORDER BY created_at ASC
"""
