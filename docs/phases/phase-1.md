# Phase 1 — Foundation Infrastructure

**Duration:** ~4 weeks
**Goal:** Working monorepo, Next.js dashboard shell, FastAPI gateway with auth, Postgres, Redis, Docker Compose, CI.

> Read [step-01-foundation-architecture.md](../plan/step-01-foundation-architecture.md) and [step-11-monorepo.md](../plan/step-11-monorepo.md) before starting.

## Acceptance criteria

You can advance to Phase 2 only when all of these pass:

- [ ] `pnpm dev` starts the full stack (web + gateway + postgres + redis) via Docker Compose
- [ ] `http://localhost:3000` shows the dashboard shell with sidebar nav
- [ ] `http://localhost:8000/docs` shows FastAPI's OpenAPI docs
- [ ] User can register, log in, log out, see their profile
- [ ] JWT auth protects `/api/v1/auth/me`
- [ ] Postgres has `users`, `sessions` tables, migrated via Alembic
- [ ] Redis is reachable from the gateway
- [ ] CI runs lint + typecheck + tests on every PR
- [ ] `git push` to a feature branch works; merging requires PR
- [ ] `.env.example` documents all needed env vars
- [ ] `README.md` has setup instructions a new dev can follow

## Task list

### Week 1: Monorepo + scaffolding

#### 1.1 Initialize the monorepo
- [ ] `pnpm init` at root
- [ ] Add `pnpm-workspace.yaml` listing `apps/*` and `packages/*`
- [ ] Add `turbo.json` with `dev`, `build`, `lint`, `typecheck`, `test` tasks
- [ ] Add root `package.json` with Turbo scripts: `pnpm dev`, `pnpm build`, etc.
- [ ] `.gitignore` (Node, Python, env files, build outputs, `data/`)
- [ ] `.editorconfig`
- [ ] `.nvmrc` pinning Node 20
- [ ] Initialize git, first commit, push to GitHub

#### 1.2 Shared packages
- [ ] `packages/tsconfig/` — base, nextjs, library tsconfigs
- [ ] `packages/eslint-config/` — base eslint config
- [ ] `packages/types/` — empty for now, with `package.json` and `tsconfig.json`
- [ ] `packages/ui/` — empty shadcn-style component library scaffold
- [ ] `packages/sdk/` — empty for now

#### 1.3 Next.js app scaffold
- [ ] `cd apps/web && pnpm create next-app .` (TypeScript, Tailwind, App Router, no src)
- [ ] Install shadcn/ui: `pnpm dlx shadcn@latest init`
- [ ] Install Zustand, TanStack Query, Lucide React
- [ ] Configure `tsconfig.json` to extend `packages/tsconfig/nextjs.json`
- [ ] Set up Tailwind dark mode
- [ ] Build a `DashboardLayout` with sidebar + topbar (use shadcn examples)
- [ ] Sidebar has placeholder routes: Dashboard, Markets, Portfolio, Backtesting, Research, Settings
- [ ] Top navbar: search box (placeholder), profile dropdown
- [ ] `/login` and `/register` pages (forms only, wired to auth in 1.6)

#### 1.4 FastAPI gateway scaffold
- [ ] `services/api-gateway/` with the layout from [step-14](../plan/step-14-folder-structures.md)
- [ ] `pyproject.toml` using `uv` (Python 3.12)
- [ ] Dependencies: fastapi, uvicorn, pydantic-settings, sqlalchemy, asyncpg, alembic, redis, python-jose, passlib[bcrypt]
- [ ] `app/main.py` with health endpoint `GET /health`
- [ ] `app/core/config.py` reading env via pydantic-settings
- [ ] `app/core/database.py` async SQLAlchemy session
- [ ] `app/core/redis.py` async Redis client
- [ ] `app/core/logging.py` structured JSON logger
- [ ] CORS middleware allowing `http://localhost:3000`
- [ ] Run with `uvicorn app.main:app --reload` and confirm `/docs` works

### Week 2: Database + auth

#### 1.5 Database setup
- [ ] Add Alembic: `alembic init alembic`
- [ ] Configure Alembic to use the SQLAlchemy URL from `core/config.py`
- [ ] `app/models/user.py` — `User` model (UUID id, email unique, username, hashed_password, full_name, role, is_active, timestamps)
- [ ] `app/models/session.py` — `Session` model (id, user_id, refresh_token_hash, ip, device_info, expires_at, created_at)
- [ ] First migration: `alembic revision --autogenerate -m "users and sessions"`
- [ ] `alembic upgrade head`

#### 1.6 Auth implementation
- [ ] `app/schemas/auth.py` — `RegisterRequest`, `LoginRequest`, `TokenResponse`, `UserResponse`
- [ ] `app/services/auth.py` — `register_user`, `authenticate`, `create_tokens`, `refresh_tokens`, `revoke_session`
- [ ] `app/repositories/users.py` — `get_by_email`, `get_by_id`, `create`
- [ ] `app/api/v1/auth.py` — routes:
  - `POST /api/v1/auth/register`
  - `POST /api/v1/auth/login`
  - `POST /api/v1/auth/refresh`
  - `POST /api/v1/auth/logout`
  - `GET /api/v1/auth/me` (protected)
- [ ] `app/dependencies/auth.py` — `get_current_user` FastAPI dependency
- [ ] JWT signing with HS256, configurable secret
- [ ] Refresh token stored hashed in DB
- [ ] Tests: `tests/integration/test_auth.py` — full register → login → refresh → me → logout flow

#### 1.7 Frontend auth wiring
- [ ] `apps/web/services/auth.ts` — typed client for auth endpoints
- [ ] `apps/web/store/auth.ts` — Zustand store for tokens + user
- [ ] `apps/web/hooks/useAuth.ts` — `login`, `logout`, `register`, `me`
- [ ] Wire `/login` and `/register` pages to the API
- [ ] Persist tokens in localStorage; refresh on app load
- [ ] Protected routes: redirect to `/login` if not authenticated
- [ ] Profile dropdown shows user email + logout button

### Week 3: Docker Compose + dev workflow

#### 1.8 Docker setup
- [ ] `services/api-gateway/Dockerfile` (multi-stage, Python 3.12 slim)
- [ ] `apps/web/Dockerfile` (multi-stage, Node 20 alpine, output: standalone)
- [ ] Root `docker-compose.yml`:
  - `web` (Next.js, port 3000)
  - `api` (FastAPI, port 8000)
  - `postgres` (port 5432, persistent volume)
  - `redis` (port 6379)
- [ ] `docker-compose.override.yml` for local dev (volumes mounted, hot reload)
- [ ] `.env.example` documenting: `DATABASE_URL`, `REDIS_URL`, `JWT_SECRET`, `JWT_REFRESH_SECRET`, `CORS_ORIGINS`
- [ ] `make up` / `make down` / `make logs` Makefile shortcuts
- [ ] Confirm full stack works: `docker compose up` → register → login → see profile

#### 1.9 Developer experience
- [ ] Pre-commit hooks via `husky` + `lint-staged`
- [ ] `pnpm lint`, `pnpm typecheck`, `pnpm test` work at root (Turbo dispatches)
- [ ] Python: ruff for lint/format, mypy for typecheck, pytest for tests
- [ ] `scripts/setup.sh` — one-command setup for new contributors
- [ ] `scripts/seed_data.py` — seeds a test user (`test@quantos.local` / `testpass123`)

### Week 4: CI/CD + polish

#### 1.10 GitHub Actions
- [ ] `.github/workflows/ci.yml` — runs on every PR:
  - Lint (eslint + ruff)
  - Typecheck (tsc + mypy)
  - Frontend tests (Vitest)
  - Backend tests (pytest with Postgres + Redis services)
  - Docker build (don't push, just verify)
- [ ] Branch protection on `main`: require PR + CI green
- [ ] `.github/PULL_REQUEST_TEMPLATE.md`
- [ ] `.github/ISSUE_TEMPLATE/bug.md` and `feature.md`
- [ ] `CODEOWNERS` file
- [ ] Dependabot config

#### 1.11 Documentation
- [ ] Update `README.md` with: project description, setup steps, common commands
- [ ] `docs/onboarding.md` — how to get a dev running in <30 min
- [ ] `docs/architecture/01-system-architecture.md` — link to step-01 with current MVP context
- [ ] `docs/architecture/02-database-schema.md` — list tables created so far
- [ ] `CONTRIBUTING.md` — branch / PR / commit conventions

#### 1.12 Acceptance check
- [ ] Run through every item in "Acceptance criteria" above
- [ ] Tag the repo: `git tag phase-1-complete && git push --tags`
- [ ] Update `docs/CURRENT_PHASE.md` to point to Phase 2

## Out of scope (don't do yet)

- ❌ Market data ingestion (Phase 2)
- ❌ Charts (Phase 2)
- ❌ Portfolio CRUD (Phase 3)
- ❌ ML models (Phase 4)
- ❌ AI assistant (Phase 6)
- ❌ Microservices beyond api-gateway (the gateway is the only service for now)
- ❌ Kubernetes
- ❌ Kafka

## Useful commands

```bash
# First time setup
./scripts/setup.sh

# Start everything
docker compose up -d

# Run frontend only
pnpm --filter web dev

# Run backend only
cd services/api-gateway && uv run uvicorn app.main:app --reload

# Generate a migration
cd services/api-gateway && alembic revision --autogenerate -m "describe change"

# Apply migrations
cd services/api-gateway && alembic upgrade head

# Run tests
pnpm test                    # all
pnpm --filter web test       # frontend only
cd services/api-gateway && uv run pytest    # backend only

# Lint + format
pnpm lint
pnpm format
```

## Common pitfalls

- **Don't add features outside Phase 1.** If you find yourself building portfolio CRUD, stop.
- **Don't skip Alembic.** Manual schema changes will bite you in Phase 2.
- **Don't put auth logic in the frontend.** All token validation happens server-side.
- **Don't commit `.env`.** Only `.env.example`.
- **Don't use `localhost` in Docker Compose service URLs** — use the service name (`postgres`, `redis`).
- **Use async SQLAlchemy.** Mixing sync and async will cause hangs.

## Definition of done for each task

- Code compiles and tests pass locally
- Code goes through a PR (even if you're solo — discipline matters)
- The acceptance criterion you're working toward actually passes
- Documentation updated if behavior changed
