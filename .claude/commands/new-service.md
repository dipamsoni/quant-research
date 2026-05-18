---
description: Scaffold a new FastAPI microservice with the standard layout
argument-hint: <service-name>
---

Scaffold a new FastAPI microservice named `$ARGUMENTS` under `services/$ARGUMENTS/`.

Before writing any code:
1. Read `docs/plan/step-14-folder-structures.md` — section "FastAPI service (every service)" for the layout
2. Read `docs/plan/step-03-microservice-architecture.md` for service conventions
3. Confirm with the user this service is appropriate for the current phase (check `docs/CURRENT_PHASE.md`)

Then create exactly this structure:

```
services/$ARGUMENTS/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI app entry
│   ├── api/
│   │   ├── __init__.py
│   │   └── v1/
│   │       └── __init__.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py           # pydantic-settings
│   │   ├── database.py         # async SQLAlchemy
│   │   ├── redis.py
│   │   └── logging.py
│   ├── middleware/
│   │   └── __init__.py
│   ├── dependencies/
│   │   ├── __init__.py
│   │   └── auth.py             # get_current_user
│   ├── schemas/
│   │   └── __init__.py
│   ├── models/
│   │   └── __init__.py
│   ├── repositories/
│   │   └── __init__.py
│   ├── services/
│   │   └── __init__.py
│   ├── workers/
│   │   └── __init__.py
│   ├── clients/
│   │   └── __init__.py
│   └── utils/
│       └── __init__.py
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── unit/
│   │   └── __init__.py
│   └── integration/
│       └── __init__.py
├── Dockerfile
├── pyproject.toml
└── README.md
```

`main.py` content: FastAPI app with `/health` endpoint, CORS middleware, structured logging, lifespan handler that initializes DB and Redis connections.

`pyproject.toml`: use `uv` style; minimum deps: fastapi, uvicorn[standard], pydantic-settings, sqlalchemy[asyncio], asyncpg, alembic, redis, structlog, httpx.

`Dockerfile`: multi-stage with Python 3.12-slim, uses uv for installs, runs as non-root.

`README.md`: brief description, how to run locally, env vars needed.

After scaffolding:
1. Update `docker-compose.yml` to include the new service
2. Update root `pnpm-workspace.yaml` if any TS package was added (none for this command)
3. Update `docs/architecture/01-system-architecture.md` and `03-service-topology.md` to mention the new service
4. Tell the user the next step is wiring routes/models for their specific feature

Do NOT add Alembic setup if the service won't own DB tables. Ask first.
