# api-gateway

FastAPI gateway for quant-os. Handles auth, CORS, and routes to downstream services.

## Setup

```bash
uv sync --dev
uv run uvicorn app.main:app --reload
```

Docs at `http://localhost:8000/docs`.

## Env vars

See `.env.example` at repo root.

## Tests

```bash
uv run pytest
```
