from fastapi import FastAPI

app = FastAPI(
    title="Dailymotion API Proxy",
    description="Proxy service for Dailymotion API with Redis caching",
    version="1.0.0",
)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}
