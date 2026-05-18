# CLAUDE.md — quant-os

You are working on **quant-os**: a modular quant platform that grows from an MVP (market dashboard, portfolio, ML signals, backtesting, AI assistant) into a multi-agent AI quant system. The full plan lives in `docs/`. Read those on demand — do not load them by default.

## Critical rules

- **YOU MUST** check `docs/CURRENT_PHASE.md` at the start of any session. Only build features for the current phase. Do not jump ahead.
- **YOU MUST** read `docs/phases/<current-phase>.md` before starting work in a new phase.
- **NEVER** create code for RL, multi-agent systems, Kubernetes, Kafka, or distributed infra during Phase 1–6. They are scoped for later phases.
- **NEVER** commit secrets. `.env*` files are gitignored. Use `.env.example` for documenting variables.
- **NEVER** push directly to `main`. Branch per task: `feat/...`, `fix/...`, `refactor/...`. Conventional Commits.
- When the user asks for a feature, build it as a **vertical slice** (UI → API → DB → tests) before moving on. Do not build all backend then all frontend.
- Prefer **reusing mature open-source libraries** over reinventing them. See `docs/architecture/12-open-source-reuse.md`.

## Stack (locked for MVP)

- **Frontend:** Next.js 15 (App Router), TypeScript, TailwindCSS, shadcn/ui, Zustand, React Query, TradingView Lightweight Charts
- **Backend:** FastAPI, Pydantic, SQLAlchemy, async
- **DB:** PostgreSQL 16 (with TimescaleDB extension for OHLCV), Redis 7
- **Vector:** pgvector (not Qdrant during MVP)
- **ML:** XGBoost, LightGBM, vectorbt, PyPortfolioOpt
- **AI:** LangGraph, LlamaIndex, OpenAI/Anthropic API
- **Infra (MVP):** Docker Compose locally; Railway/Render/Fly for hosting
- **Infra (later):** Kubernetes, Kafka — Phase 11+, NOT before

## Repo map

- `apps/web/` — Next.js app (the institutional dashboard UI)
- `services/` — FastAPI microservices (`api-gateway`, `market-data`, `portfolio`, `prediction`, `backtesting`, `agent`, `analytics`)
- `packages/` — shared TS code (`ui`, `types`, `sdk`, `config`)
- `ai/` — Python AI code (`agents`, `rag`, `models`, `prompts`)
- `infra/` — Docker, k8s manifests (later), Terraform (later)
- `docs/` — the full project plan, phase guides, architecture references
- `data/` — datasets, model registry, checkpoints (gitignored)

## Workflow

- Run `pnpm dev` at the root for the full local stack (Turborepo orchestrates)
- Run `pnpm --filter web dev` for just the frontend
- Run `pnpm --filter <service> dev` for a single backend service
- After backend code changes: `uv run pytest` (or `pytest` inside the service dir)
- After TS changes: `pnpm typecheck && pnpm lint`
- Before any commit: tests must pass

## How to find context

- Project plan steps: `docs/plan/step-<N>-<topic>.md` (1–16, the original architecture)
- Current phase tasks: `docs/phases/phase-<N>.md`
- Architecture deep-dives: `docs/architecture/<topic>.md`
- Database schema reference: `docs/architecture/02-database-schema.md`
- API contracts: `docs/architecture/04-api-contracts.md`

Use `@docs/phases/phase-1.md` style imports only when the user asks about that phase. Otherwise, read on demand with the file tools.

## Subagents available

- `quant-researcher` — for ML/quant strategy questions, feature engineering, backtesting design
- `infra-engineer` — for Docker, deployment, observability, CI/CD
- `frontend-architect` — for Next.js, component design, charting

Invoke with the Task tool when a question is squarely in their domain.

## Slash commands available

- `/phase-status` — show current phase, completed tasks, next task
- `/new-service <name>` — scaffold a FastAPI microservice with the standard layout
- `/new-feature <name>` — start a vertical slice (creates branch, planning doc, todo list)
- `/db-migrate <description>` — generate an Alembic migration
- `/review-plan` — load and summarize the relevant plan step before working

## What good looks like

- A focused PR that completes one vertical slice with tests
- Code that follows existing patterns in the repo (read neighboring files first)
- Database changes accompanied by a migration
- New API endpoints documented in OpenAPI (FastAPI does this automatically)
- New components placed in `packages/ui/` if reusable, `apps/web/components/` if app-specific

## What bad looks like

- Touching multiple phases of work in one PR
- Building infra for problems we don't have yet (over-engineering)
- Adding a new dependency without checking if `packages/` already has it
- Mock data hardcoded in components instead of fetched from the SDK

## When in doubt

Ask. A clarifying question is cheaper than rewriting half a service.
