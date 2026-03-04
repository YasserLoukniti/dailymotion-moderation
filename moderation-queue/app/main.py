from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI

from app.database.connection import get_pool, close_pool
from app.database.migrations import run_migrations

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.

    Handles startup and shutdown events:
    - Startup: Initialize database pool and run migrations
    - Shutdown: Close database pool
    """
    # Startup
    logger.info("Starting application")
    await get_pool()
    await run_migrations()
    logger.info("Application started successfully")

    yield

    # Shutdown
    logger.info("Shutting down application")
    await close_pool()
    logger.info("Application shut down successfully")


app = FastAPI(
    title="Moderation Queue API",
    description="Video moderation queue management system",
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}
