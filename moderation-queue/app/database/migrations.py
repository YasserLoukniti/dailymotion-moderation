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
    sql_file = Path(__file__).parent.parent.parent.parent / "scripts" / "init.sql"

    if not sql_file.exists():
        logger.warning(f"Migration file not found: {sql_file}")
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
