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

## Problems Encountered

### 1. `FOR UPDATE SKIP LOCKED` locks all rows during `ORDER BY` (MySQL/InnoDB)

The naive approach — `SELECT ... ORDER BY created_at LIMIT 1 FOR UPDATE SKIP LOCKED` — doesn't work as expected on MySQL. InnoDB scans and locks **all candidate rows** during the sort, not just the one returned by `LIMIT 1`. With 10 concurrent moderators, only the first one got a video; the other 9 saw an empty queue.

**Fix:** Two-step approach — first get candidate IDs without locking, then try to lock each one individually with `FOR UPDATE SKIP LOCKED`. This lets concurrent transactions skip already-locked rows properly.

### 2. Stale reads with `autocommit=False` (MySQL REPEATABLE READ)

With `autocommit=False`, every connection implicitly starts a long-lived transaction. Under MySQL's default `REPEATABLE READ` isolation, read-only queries kept seeing a snapshot from transaction start — so `GET /log_video` didn't return recently inserted log entries.

**Fix:** Set `autocommit=True` on the connection pool. Each read gets a fresh snapshot, and explicit `BEGIN`/`COMMIT` are used only where transactions are needed (inserts, updates).

### 3. pytest-asyncio event loop mismatch

A session-scoped database pool fixture created the pool on test 1's event loop. Test 2 got a different loop → `RuntimeError: Future attached to a different loop`. This is a common pitfall with `pytest-asyncio`.

**Fix:** `asyncio_default_fixture_loop_scope = function` in `pytest.ini` + reset the global pool before each test so every test gets its own clean connection.

### 4. `TRUNCATE TABLE` deadlocks in test cleanup

`TRUNCATE TABLE` requires a table-level lock, but the app's connection pool kept open transactions — tests hung indefinitely waiting for the lock.

**Fix:** Use `DELETE FROM` instead of `TRUNCATE` in test teardown. Slightly slower, but avoids lock conflicts entirely.

### 5. Missing `Authorization` header returns 422 instead of 401

FastAPI's `Header(...)` (required) returns a 422 validation error when the header is missing, which isn't semantically correct.

**Fix:** Use `Header(default=None)` with an explicit `None` check to return a proper 401 Unauthorized.

## Possible Improvements

- **Message queue for video ingestion** — Replace the synchronous `POST /add_video` with a consumer reading from RabbitMQ or Kafka. This decouples video upload from moderation, absorbs traffic spikes, and allows retry/dead-letter handling for failed inserts
- **Distributed tracing (Datadog APM)** — Follow requests across both services with `dd-trace-py`; Dailymotion already uses Datadog in production
- **Structured logging** — JSON logs with correlation IDs, ready for Datadog Log Management ingestion
- **Rate limiting** — Per-moderator rate limiting on `GET /get_video` to prevent abuse (e.g., via `slowapi` or Redis-based token bucket)
- **Connection pool monitoring** — Expose pool stats (active/idle connections) as metrics to detect pool exhaustion early
- **Pagination on `GET /log_video`** — For videos with a long moderation history, add `?limit=` and `?offset=` query params
- **Circuit breaker on the proxy** — If Dailymotion API is down, fail fast instead of accumulating timeouts (e.g., `circuitbreaker` library)
- **WebSocket notifications** — Push events when new videos enter the queue, instead of requiring moderators to poll
