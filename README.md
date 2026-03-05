# Dailymotion Moderation Tool

Backend tool to track moderation actions on uploaded videos. Two microservices: a **Moderation Queue API** (video lifecycle management) and a **Dailymotion API Proxy** (video info with caching).

## Architecture

See [architecture.md](./architecture.md) for the full system diagram.

```
                    Moderation Console UI (not built by us)
                       /                    \
                     /                        \
                   /                            \
    Moderation Queue API (port 8000)    Dailymotion API Proxy (port 8001)
         FastAPI + MySQL                     FastAPI + Redis
         * POST /add_video                   * GET /get_video_info/{video_id}
         * GET  /get_video
         * POST /flag_video
         * GET  /stats
         * GET  /log_video/{video_id}
```

## Prerequisites

- Docker
- Docker Compose

## Quick Start

```bash
git clone <repo_url>
cd dailymotion-moderation
docker-compose up --build
```

The services will be available at:
- Moderation Queue API: http://localhost:8000
- Dailymotion API Proxy: http://localhost:8001
- Swagger UI (Queue): http://localhost:8000/docs
- Swagger UI (Proxy): http://localhost:8001/docs

## Running Tests

```bash
# Moderation Queue tests
docker-compose exec moderation-queue python -m pytest tests/ -v

# Dailymotion Proxy tests
docker-compose exec dailymotion-proxy python -m pytest tests/ -v
```

## API Usage Examples

```bash
# Add a video to the moderation queue
curl -XPOST http://localhost:8000/add_video -H 'Content-Type: application/json' -d '{"video_id": 123456}'

# Get next video to moderate (base64 of "john.doe" = "am9obi5kb2U=")
curl -XGET http://localhost:8000/get_video -H 'Authorization: am9obi5kb2U='

# Flag a video
curl -XPOST http://localhost:8000/flag_video -H 'Content-Type: application/json' -H 'Authorization: am9obi5kb2U=' -d '{"video_id": 123456, "status": "spam"}'

# Get queue statistics
curl -XGET http://localhost:8000/stats

# Get moderation history
curl -XGET http://localhost:8000/log_video/123456

# Get video info (proxied from Dailymotion API)
curl -XGET http://localhost:8001/get_video_info/123456
```

## Technical Choices

- **FastAPI** — Async framework, matches Dailymotion's Python stack
- **MySQL 8.0** — ACID-compliant DBMS with `FOR UPDATE SKIP LOCKED` for concurrent queue processing
- **Redis 7** — In-memory cache for API proxy responses (TTL 300s)
- **aiomysql** — Async MySQL driver, raw SQL only (no ORM as per requirements)
- **httpx** — Async HTTP client for Dailymotion API calls
- **Repository pattern** — Clean separation: routes (thin) -> services (business logic) -> repositories (data access)
- **Docker healthchecks** — Services start in the right order with `depends_on` + `condition: service_healthy`

## Concurrency Handling

Multiple moderators can work simultaneously. The `GET /get_video` endpoint uses a two-step locking approach with `SELECT ... FOR UPDATE SKIP LOCKED` to ensure no two moderators ever receive the same video, even under concurrent load.

## Possible Improvements

- Distributed tracing (Datadog APM) to follow requests across both services
- Prometheus/Datadog metrics for queue monitoring and alerting
- Rate limiting on API endpoints
- WebSocket notifications when new videos enter the queue
