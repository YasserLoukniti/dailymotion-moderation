# Architecture

## System Overview

```mermaid
graph TB
    UI[Moderation Console UI<br/>Frontend - Not built by us]

    subgraph "Docker Compose Network"
        MQ[Moderation Queue API<br/>FastAPI :8000]
        DP[Dailymotion API Proxy<br/>FastAPI :8001]
        DB[(MySQL 8.0<br/>Videos + Logs)]
        RD[(Redis 7<br/>Cache Layer)]
    end

    DM[Dailymotion Public API<br/>api.dailymotion.com]

    UI -- "POST /add_video<br/>GET /get_video<br/>POST /flag_video<br/>GET /stats<br/>GET /log_video/:id" --> MQ
    UI -- "GET /get_video_info/:id" --> DP

    MQ -- "aiomysql<br/>Raw SQL" --> DB
    DP -- "Redis cache<br/>TTL 300s" --> RD
    DP -- "httpx<br/>GET /video/xa0apeu" --> DM

    style UI fill:#4a9eff,color:#fff
    style MQ fill:#2d8659,color:#fff
    style DP fill:#2d8659,color:#fff
    style DB fill:#00758f,color:#fff
    style RD fill:#dc382d,color:#fff
    style DM fill:#0d6efd,color:#fff
```

## Moderation Queue — Internal Architecture

```mermaid
graph LR
    subgraph "Routes (thin)"
        R[moderation.py]
    end

    subgraph "Services (business logic)"
        S[moderation_service.py]
    end

    subgraph "Repositories (data access)"
        RP[video_repository.py]
    end

    subgraph "Database"
        Q[queries.py<br/>Raw SQL constants]
        C[connection.py<br/>aiomysql pool]
    end

    R --> S --> RP --> Q
    RP --> C
```

## Database Schema

```mermaid
erDiagram
    videos {
        int id PK
        bigint video_id UK
        varchar status
        varchar assigned_moderator
        timestamp created_at
        timestamp updated_at
    }

    moderation_logs {
        int id PK
        bigint video_id FK
        varchar status
        varchar moderator
        timestamp created_at
    }

    videos ||--o{ moderation_logs : "has many"
```

## Concurrency Model

When multiple moderators call `GET /get_video` simultaneously:

1. **Check existing assignment** — If the moderator already has a pending video, return it (idempotent)
2. **Get candidates** — `SELECT video_id ... WHERE status='pending' AND assigned_moderator IS NULL` (no lock)
3. **Lock one** — For each candidate, `SELECT ... WHERE video_id=X FOR UPDATE SKIP LOCKED`
4. **Assign** — `UPDATE ... SET assigned_moderator=moderator`

This two-step approach avoids MySQL/InnoDB locking all candidate rows during `ORDER BY` scans.

## Proxy Caching Flow

```mermaid
flowchart TD
    A[GET /get_video_info/:id] --> B{video_id ends with 404?}
    B -- Yes --> C[HTTP 404]
    B -- No --> D{Redis cache hit?}
    D -- Yes --> E[Return cached data]
    D -- No --> F[Fetch from Dailymotion API]
    F --> G{Success?}
    G -- Yes --> H[Cache in Redis TTL=300s]
    H --> I[Return data]
    G -- Timeout --> J[HTTP 504]
    G -- Error --> K[HTTP 502]
```
