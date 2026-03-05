import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.services.cache_service import close_redis
from app.routes.proxy import router as proxy_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    logger.info("Starting Dailymotion API Proxy")
    yield
    logger.info("Shutting down Dailymotion API Proxy")
    await close_redis()


app = FastAPI(
    title="Dailymotion API Proxy",
    description="Proxy service for Dailymotion API with Redis caching",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(proxy_router)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}
