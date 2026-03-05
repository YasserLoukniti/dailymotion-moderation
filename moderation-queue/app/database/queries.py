"""
Raw SQL queries for the moderation system.

All queries are defined as constants to maintain visibility and control
over database operations (no ORM as per requirements).

NOTE: MySQL uses %s for parameter placeholders (not $1, $2 like PostgreSQL)
"""

# ============================================================================
# VIDEO QUERIES
# ============================================================================

INSERT_VIDEO = """
INSERT INTO videos (video_id, status, created_at, updated_at)
VALUES (%s, 'pending', NOW(), NOW())
"""

GET_LAST_INSERT_ID = """
SELECT LAST_INSERT_ID() as id
"""

CHECK_VIDEO_EXISTS = """
SELECT video_id FROM videos WHERE video_id = %s
"""

GET_MODERATOR_ASSIGNED_VIDEO = """
SELECT video_id FROM videos
WHERE assigned_moderator = %s AND status = 'pending'
LIMIT 1
"""

GET_NEXT_PENDING_VIDEO_FOR_UPDATE = """
SELECT video_id FROM videos
WHERE status = 'pending' AND assigned_moderator IS NULL
ORDER BY created_at ASC
LIMIT 1
FOR UPDATE SKIP LOCKED
"""

GET_NEXT_PENDING_VIDEO_IDS = """
SELECT video_id FROM videos
WHERE status = 'pending' AND assigned_moderator IS NULL
ORDER BY created_at ASC
LIMIT 10
"""

LOCK_VIDEO_FOR_UPDATE = """
SELECT video_id FROM videos
WHERE video_id = %s AND status = 'pending' AND assigned_moderator IS NULL
FOR UPDATE SKIP LOCKED
"""

ASSIGN_VIDEO_TO_MODERATOR = """
UPDATE videos
SET assigned_moderator = %s, updated_at = NOW()
WHERE video_id = %s
"""

GET_VIDEO_BY_ID = """
SELECT id, video_id, status, assigned_moderator, created_at, updated_at
FROM videos
WHERE video_id = %s
"""

UPDATE_VIDEO_STATUS = """
UPDATE videos
SET status = %s, assigned_moderator = NULL, updated_at = NOW()
WHERE video_id = %s
"""

# ============================================================================
# STATS QUERIES
# ============================================================================

GET_STATS = """
SELECT
    SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) AS total_pending_videos,
    SUM(CASE WHEN status = 'spam' THEN 1 ELSE 0 END) AS total_spam_videos,
    SUM(CASE WHEN status = 'not spam' THEN 1 ELSE 0 END) AS total_not_spam_videos
FROM videos
"""

# ============================================================================
# MODERATION LOG QUERIES
# ============================================================================

INSERT_MODERATION_LOG = """
INSERT INTO moderation_logs (video_id, status, moderator, created_at)
VALUES (%s, %s, %s, NOW())
"""

GET_VIDEO_LOGS = """
SELECT created_at AS date, status, moderator
FROM moderation_logs
WHERE video_id = %s
ORDER BY created_at ASC
"""
