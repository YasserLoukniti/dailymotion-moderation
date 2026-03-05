import aiomysql
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime

from app.database.connection import get_pool
from app.database import queries
from app.models.enums import VideoStatus
from app.config import settings

logger = logging.getLogger(__name__)


class VideoRepository:
    """
    Data access layer for video operations.
    All database interactions use raw SQL (no ORM).
    """

    def __init__(self):
        self.pool: Optional[aiomysql.Pool] = None

    async def _get_pool(self) -> aiomysql.Pool:
        """Get the database connection pool."""
        if self.pool is None:
            self.pool = await get_pool()
        return self.pool

    async def add_video(self, video_id: int) -> Dict[str, Any]:
        """
        Add a new video to the moderation queue.

        Args:
            video_id: The video ID to add

        Returns:
            Dict containing the created video data

        Raises:
            aiomysql.IntegrityError: If video_id already exists
        """
        pool = await self._get_pool()

        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                # Start transaction to insert video and initial log entry
                await conn.begin()

                try:
                    # Insert video
                    await cursor.execute(queries.INSERT_VIDEO, (video_id,))

                    # Insert initial moderation log (status=pending, moderator=null)
                    await cursor.execute(
                        queries.INSERT_MODERATION_LOG,
                        (video_id, VideoStatus.PENDING.value, None)
                    )

                    await conn.commit()
                    logger.info(f"Added video {video_id} to moderation queue")

                    return {
                        "video_id": video_id,
                        "status": VideoStatus.PENDING.value
                    }
                except Exception as e:
                    await conn.rollback()
                    raise

    async def check_video_exists(self, video_id: int) -> bool:
        """
        Check if a video exists in the database.

        Args:
            video_id: The video ID to check

        Returns:
            True if video exists, False otherwise
        """
        pool = await self._get_pool()

        async with pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(queries.CHECK_VIDEO_EXISTS, (video_id,))
                row = await cursor.fetchone()
                return row is not None

    async def get_video_by_id(self, video_id: int) -> Optional[Dict[str, Any]]:
        """
        Get a video by its ID.

        Args:
            video_id: The video ID to retrieve

        Returns:
            Video data dict or None if not found
        """
        pool = await self._get_pool()

        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute(queries.GET_VIDEO_BY_ID, (video_id,))
                row = await cursor.fetchone()
                return row if row else None

    async def get_moderator_assigned_video(self, moderator: str) -> Optional[int]:
        """
        Get the video currently assigned to a moderator.

        Args:
            moderator: The moderator name

        Returns:
            video_id if found, None otherwise
        """
        pool = await self._get_pool()

        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute(
                    queries.GET_MODERATOR_ASSIGNED_VIDEO,
                    (moderator,)
                )
                row = await cursor.fetchone()
                return row['video_id'] if row else None

    async def assign_next_video(self, moderator: str) -> Optional[int]:
        """
        Assign the next pending video to a moderator using SELECT FOR UPDATE SKIP LOCKED.

        Uses a two-step approach to avoid MySQL locking all candidate rows
        during ORDER BY scans:
        1. Get candidate video IDs (no lock)
        2. Try to lock each candidate individually with SKIP LOCKED

        Args:
            moderator: The moderator name to assign the video to

        Returns:
            video_id if a video was assigned, None if queue is empty
        """
        pool = await self._get_pool()

        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                await conn.begin()

                try:
                    # Step 1: Get candidate video IDs without locking
                    await cursor.execute(queries.GET_NEXT_PENDING_VIDEO_IDS, (settings.candidate_batch_size,))
                    candidates = await cursor.fetchall()

                    if not candidates:
                        await conn.commit()
                        logger.info("No pending videos available in queue")
                        return None

                    # Step 2: Try to lock each candidate one by one
                    for candidate in candidates:
                        vid = candidate['video_id']
                        await cursor.execute(queries.LOCK_VIDEO_FOR_UPDATE, (vid,))
                        row = await cursor.fetchone()
                        if row is not None:
                            # Successfully locked this video
                            await cursor.execute(
                                queries.ASSIGN_VIDEO_TO_MODERATOR,
                                (moderator, vid)
                            )
                            await conn.commit()
                            logger.info(f"Assigned video {vid} to moderator {moderator}")
                            return vid

                    # All candidates were locked by other transactions
                    await conn.commit()
                    logger.info("No pending videos available in queue")
                    return None

                except Exception as e:
                    await conn.rollback()
                    raise

    async def update_video_status(
        self,
        video_id: int,
        status: str,
        moderator: str
    ) -> Optional[Dict[str, Any]]:
        """
        Update video status and log the moderation action.

        Args:
            video_id: The video ID to update
            status: New status ('spam' or 'not spam')
            moderator: The moderator who flagged the video

        Returns:
            Updated video data or None if not found
        """
        pool = await self._get_pool()

        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                await conn.begin()

                try:
                    # Update video status
                    await cursor.execute(
                        queries.UPDATE_VIDEO_STATUS,
                        (status, video_id)
                    )

                    if cursor.rowcount == 0:
                        await conn.rollback()
                        return None

                    # Insert moderation log
                    await cursor.execute(
                        queries.INSERT_MODERATION_LOG,
                        (video_id, status, moderator)
                    )

                    await conn.commit()
                    logger.info(f"Video {video_id} flagged as '{status}' by {moderator}")

                    return {
                        "video_id": video_id,
                        "status": status
                    }

                except Exception as e:
                    await conn.rollback()
                    raise

    async def get_stats(self) -> Dict[str, int]:
        """
        Get moderation statistics.

        Returns:
            Dict with counts for pending, spam, and not spam videos
        """
        pool = await self._get_pool()

        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute(queries.GET_STATS)
                row = await cursor.fetchone()
                # Handle NULL values from SUM (when table is empty)
                return {
                    'total_pending_videos': row['total_pending_videos'] or 0,
                    'total_spam_videos': row['total_spam_videos'] or 0,
                    'total_not_spam_videos': row['total_not_spam_videos'] or 0,
                }

    async def get_video_logs(self, video_id: int) -> List[Dict[str, Any]]:
        """
        Get moderation history for a video.

        Args:
            video_id: The video ID to get logs for

        Returns:
            List of log entries ordered by date
        """
        pool = await self._get_pool()

        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute(queries.GET_VIDEO_LOGS, (video_id,))
                rows = await cursor.fetchall()
                return list(rows)
