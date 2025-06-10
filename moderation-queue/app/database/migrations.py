import logging
from pathlib import Path

from app.database.connection import get_pool

logger = logging.getLogger(__name__)


async def run_migrations() -> None:
    """
    Run database migrations by executing init.sql schema.

    This is called on application startup to ensure the database schema
    is initialized. The SQL file is idempotent (uses CREATE IF NOT EXISTS).
    """
    pool = await get_pool()

    # Read the SQL schema file
    # Check multiple possible locations (local dev vs Docker container)
    possible_paths = [
        Path(__file__).parent.parent.parent.parent / "scripts" / "init.sql",
        Path("/app/scripts/init.sql"),
    ]

    sql_file = None
    for path in possible_paths:
        if path.exists():
            sql_file = path
            break

    if sql_file is None:
        logger.warning("Migration file not found, schema may already be initialized by Docker")
        return

    logger.info(f"Running migrations from {sql_file}")

    sql_content = sql_file.read_text(encoding="utf-8")

    # Split SQL statements (MySQL doesn't support multiple statements in one execute)
    statements = [stmt.strip() for stmt in sql_content.split(';') if stmt.strip()]

    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            for statement in statements:
                if statement:
                    await cursor.execute(statement)
            await conn.commit()

    logger.info("Migrations completed successfully")
