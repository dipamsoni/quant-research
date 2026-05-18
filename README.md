# quant-os

A modular AI-powered quant research and portfolio platform.

## Status

**Phase 1 — Foundation Infrastructure** (active)

See [`docs/CURRENT_PHASE.md`](docs/CURRENT_PHASE.md) for the active phase and [`docs/INDEX.md`](docs/INDEX.md) for the full project plan.

## What this is

quant-os grows in stages from an MVP (live market dashboard, portfolio tracker, ML signals, backtesting, AI research assistant) into a multi-agent quant platform with reinforcement learning. Each phase ships as a complete, demoable product.

The MVP (Phases 1–6, ~6 months) is a usable product on its own. Phases 7–12 are upside.

## Stack (MVP)

- **Frontend:** Next.js 15 (App Router), TypeScript, TailwindCSS, shadcn/ui, Zustand, TanStack Query
- **Charts:** TradingView Lightweight Charts, ECharts, Tremor
- **Backend:** FastAPI, Pydantic, async SQLAlchemy, Alembic
- **Database:** PostgreSQL 16 + TimescaleDB extension + pgvector
- **Cache / pub/sub:** Redis 7
- **ML:** XGBoost, LightGBM, vectorbt, PyPortfolioOpt
- **AI:** LangGraph, LlamaIndex, OpenAI / Anthropic
- **Infra (MVP):** Docker Compose locally; Vercel + Railway/Render hosted
- **Infra (Phase 11+):** Kubernetes, Kafka/Redpanda, Prometheus + Grafana

## Repository layout

```
quant-os/
├── apps/web/              # Next.js dashboard
├── services/              # FastAPI microservices
│   └── api-gateway/
├── packages/              # Shared TS code (ui, types, sdk, config, eslint, tsconfig)
├── ai/                    # Python AI/ML code (importable by services)
├── infra/                 # Docker, k8s (later), terraform (later)
├── docs/                  # Full project plan + phase guides + architecture
├── data/                  # Datasets, model registry (gitignored)
├── scripts/               # Repo-wide scripts
├── .claude/               # Claude Code config (CLAUDE.md, commands, agents)
├── .github/workflows/     # CI/CD
├── docker-compose.yml
├── pnpm-workspace.yaml
├── turbo.json
├── package.json
├── CLAUDE.md
└── README.md
```

## Setup

### Prerequisites
- Node.js 20+ (`.nvmrc` provided)
- pnpm 9+
- Python 3.12+
- [uv](https://github.com/astral-sh/uv) (Python package manager)
- Docker + Docker Compose

### First-time setup
```bash
# Clone
git clone <repo-url> quant-os
cd quant-os

# Install JS deps
pnpm install

# Install Python deps for the gateway
cd services/api-gateway && uv sync && cd ../..

# Copy env vars
cp .env.example .env
# Edit .env with your secrets (JWT_SECRET, etc.)

# Start services
docker compose up -d

# Run migrations
cd services/api-gateway && uv run alembic upgrade head && cd ../..

# Seed a test user (optional)
python scripts/seed_data.py

# Open the app
open http://localhost:3000
```

### Daily commands
```bash
# Full stack
docker compose up

# Frontend only
pnpm --filter web dev

# Backend only
cd services/api-gateway && uv run uvicorn app.main:app --reload

# Tests
pnpm test                  # all
pnpm --filter web test     # frontend
cd services/api-gateway && uv run pytest    # backend

# Lint + format
pnpm lint
pnpm format

# Type check
pnpm typecheck

# Generate a migration
cd services/<service> && uv run alembic revision --autogenerate -m "describe change"
```

## Working with Claude Code

This repo is set up for Claude Code. The `.claude/` folder contains:
- `CLAUDE.md` (project root) — top-level project context
- `.claude/commands/` — slash commands (`/phase-status`, `/new-service`, `/new-feature`, `/db-migrate`, `/review-plan`)
- `.claude/agents/` — specialized subagents (`quant-researcher`, `infra-engineer`, `frontend-architect`)

When you start a Claude Code session, type `/phase-status` to orient yourself.

## Documentation

- [`docs/INDEX.md`](docs/INDEX.md) — master index
- [`docs/CURRENT_PHASE.md`](docs/CURRENT_PHASE.md) — active phase
- [`docs/plan/`](docs/plan/) — the original 16-step architecture plan
- [`docs/phases/`](docs/phases/) — actionable per-phase task lists
- [`docs/architecture/`](docs/architecture/) — topical deep-dives

## Contributing

See [`CONTRIBUTING.md`](CONTRIBUTING.md).

## License

TBD.
