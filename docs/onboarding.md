# Onboarding

Goal: get a new contributor (or future-you) productive in under 30 minutes.

## 1. Install prerequisites

- **Node.js 20+** — https://nodejs.org (or via nvm: `nvm install`)
- **pnpm 9+** — `npm install -g pnpm`
- **Python 3.12** — https://python.org or pyenv
- **uv** — `curl -LsSf https://astral.sh/uv/install.sh | sh`
- **Docker + Docker Compose** — https://docker.com
- **Git** — `git --version`

## 2. Clone and bootstrap

```bash
git clone <repo-url> quant-os
cd quant-os
./scripts/setup.sh
```

The setup script will:
- Verify prerequisites
- Install JS deps (`pnpm install`)
- Install Python deps for api-gateway (`uv sync`)
- Copy `.env.example` to `.env`
- Start Postgres + Redis
- Run migrations

## 3. Configure secrets

Edit `.env`:

```bash
# Generate strong secrets
openssl rand -hex 32  # Use for JWT_SECRET
openssl rand -hex 32  # Use for JWT_REFRESH_SECRET
openssl rand -hex 32  # Use for INTERNAL_SERVICE_TOKEN
```

For Phase 2+ you'll also need free-tier API keys from:
- AlphaVantage — https://www.alphavantage.co/support/#api-key
- Polygon — https://polygon.io (optional, paid for real-time)
- Finnhub — https://finnhub.io (optional, free tier)

## 4. Start the stack

```bash
docker compose up
```

Or run frontend and backend separately for faster iteration:

```bash
# Terminal 1 — backend
cd services/api-gateway
uv run uvicorn app.main:app --reload

# Terminal 2 — frontend
pnpm --filter web dev
```

## 5. Verify

- Frontend: http://localhost:3000
- API docs: http://localhost:8000/docs
- Health: http://localhost:8000/health

## 6. Read the project plan

- [`docs/CURRENT_PHASE.md`](CURRENT_PHASE.md) — what we're building right now
- [`docs/INDEX.md`](INDEX.md) — full plan index
- [`docs/phases/phase-1.md`](phases/phase-1.md) — start here

## 7. Use Claude Code (optional but recommended)

This repo is configured for Claude Code:

```bash
# In the project root
claude
```

Then try:
- `/phase-status` — orient yourself
- `/review-plan` — load the relevant plan step

Subagents available:
- `quant-researcher` — ML and strategy questions
- `infra-engineer` — infra, deployment, observability
- `frontend-architect` — UI implementation

## 8. Make your first change

1. Pick a task from `docs/phases/phase-1.md` (the active phase)
2. Branch: `git checkout -b feat/<short-name>`
3. Build a vertical slice: UI + API + DB + tests
4. Run checks: `make test && make lint && make typecheck`
5. Open a PR

## 9. Common issues

**`docker compose up` hangs on Postgres**
The TimescaleDB image takes ~30s to initialize on first run. Be patient.

**Migrations fail with "extension not found"**
TimescaleDB and pgvector extensions need to be created. Migrations should do this; if not, check that you're using the `timescale/timescaledb-ha` image.

**Frontend can't reach the API**
Check `NEXT_PUBLIC_API_URL` in `.env`. In Docker Compose use `http://api:8000` for inter-container, `http://localhost:8000` from your browser.

**Port 5432 already in use**
You probably have another Postgres running. Stop it: `brew services stop postgresql` or change the port in `docker-compose.yml`.

**Python deps fail to install**
You're probably not using `uv`. The repo standardizes on uv: `pip install uv` then `uv sync`.

## 10. Where to ask questions

- Open a Discussion or Issue
- Tag the area in your question (frontend, backend, ML, infra)
- For "is this in scope" questions, reference `docs/CURRENT_PHASE.md`
