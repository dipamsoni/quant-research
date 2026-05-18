# Step 11 — Professional GitHub Monorepo Setup

> Reference for repo structure, tooling, and conventions.

## Why monorepo

| Feature | Monorepo wins |
|---------|---------------|
| Shared types between FE/BE | ✅ |
| Shared SDKs | ✅ |
| Coordinated releases | ✅ |
| Single CI pipeline | ✅ |
| Easier refactors | ✅ |

## Stack

| Tool | Purpose |
|------|---------|
| Turborepo | JS/TS orchestration |
| pnpm | Package manager |
| uv | Python package manager (or Poetry, but uv is faster) |
| TypeScript | All frontend + shared packages |
| Python 3.12 | Backend services |
| Docker | Containers |
| GitHub Actions | CI/CD |

## Top-level structure

```
quant-os/
├── apps/
│   ├── web/              # Next.js dashboard
│   ├── admin/            # (later) admin UI
│   └── docs/             # (later) docs site
├── services/             # FastAPI microservices
│   ├── api-gateway/
│   ├── market-data-service/
│   ├── portfolio-service/
│   ├── prediction-service/
│   ├── backtesting-service/
│   ├── agent-service/
│   ├── rl-service/         # Phase 8
│   └── analytics-service/  # Phase 7
├── packages/             # Shared TS code
│   ├── ui/               # shared component library
│   ├── types/            # shared TS types (mirrors Pydantic models)
│   ├── sdk/              # typed API clients
│   ├── config/           # shared configs
│   ├── eslint-config/
│   └── tsconfig/
├── ai/                   # Python AI/ML code (importable by services)
│   ├── agents/
│   ├── rag/
│   ├── models/
│   ├── prompts/
│   └── reinforcement/    # Phase 8
├── infra/
│   ├── docker/
│   ├── kubernetes/       # Phase 11
│   ├── terraform/        # Phase 11
│   └── scripts/
├── data/                 # gitignored
│   ├── datasets/
│   ├── feature-store/
│   ├── model-registry/
│   └── checkpoints/
├── docs/                 # this folder
├── scripts/              # repo-wide scripts
├── .github/workflows/
├── .claude/              # Claude Code config
├── turbo.json
├── pnpm-workspace.yaml
├── package.json
├── docker-compose.yml
├── README.md
└── CLAUDE.md
```

## `pnpm-workspace.yaml`

```yaml
packages:
  - "apps/*"
  - "packages/*"
```

## `turbo.json`

```json
{
  "$schema": "https://turbo.build/schema.json",
  "tasks": {
    "build":     { "dependsOn": ["^build"], "outputs": [".next/**", "dist/**"] },
    "dev":       { "cache": false, "persistent": true },
    "lint":      { "dependsOn": ["^lint"] },
    "typecheck": { "dependsOn": ["^typecheck"] },
    "test":      { "dependsOn": ["^build"] }
  }
}
```

## Branch strategy

Trunk-based. Branches:
- `main` (production)
- `feat/*`, `fix/*`, `refactor/*`, `chore/*`

PR required to merge to `main`. Squash merge.

## Commit conventions

[Conventional Commits](https://www.conventionalcommits.org/):

```
feat(market-data): add OHLCV ingestion from Polygon
fix(portfolio): correct PnL calculation for short positions
refactor(api-gateway): extract auth middleware
docs: update phase 2 acceptance criteria
chore(deps): bump fastapi to 0.115
```

## Code quality tools

**Frontend:**
- ESLint + `@typescript-eslint`
- Prettier
- TypeScript strict mode
- Husky + lint-staged for pre-commit

**Backend:**
- Ruff (linter + formatter)
- mypy (type checking)
- pytest

## Pre-commit hooks

```
pre-commit:
  - lint
  - format
  - typecheck
  - unit tests for changed files
```

## CI workflows (`.github/workflows/`)

- `ci.yml` — runs on every PR (lint, typecheck, test)
- `frontend.yml` — builds and tests apps/web
- `backend.yml` — builds and tests services/
- `deploy-staging.yml` — runs on merge to main
- `deploy-production.yml` — runs on tag push

## Repo security

- Branch protection on `main` (required reviews, status checks)
- Dependabot for dependency updates
- CodeQL for security scanning
- Secret scanning enabled

## Required files

- `README.md`
- `CLAUDE.md`
- `LICENSE`
- `.gitignore`
- `.github/CODEOWNERS`
- `.github/PULL_REQUEST_TEMPLATE.md`
- `.github/ISSUE_TEMPLATE/bug.md`
- `.github/ISSUE_TEMPLATE/feature.md`

## See also

- [Phase 1: bootstrap monorepo](../phases/phase-1.md)
