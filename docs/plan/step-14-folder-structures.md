# Step 14 — Exact Folder Structures for Every Service

> Reference doc. Each pattern below is enforced by the `/new-service` slash command.

## Frontend (`apps/web/`)

```
apps/web/
├── app/                       # Next.js App Router
│   ├── (auth)/                # auth route group
│   │   ├── login/
│   │   └── register/
│   ├── (dashboard)/           # dashboard route group
│   │   ├── layout.tsx
│   │   ├── dashboard/
│   │   ├── market/
│   │   ├── portfolio/
│   │   ├── backtesting/
│   │   ├── research/
│   │   ├── analytics/
│   │   └── settings/
│   ├── api/                   # Next.js API routes (rare; prefer FastAPI)
│   ├── layout.tsx
│   ├── page.tsx
│   └── globals.css
├── components/
│   ├── charts/
│   ├── trading/
│   ├── portfolio/
│   ├── analytics/
│   ├── ai/
│   ├── layouts/
│   ├── tables/
│   ├── forms/
│   └── ui/                    # app-specific (truly reusable → packages/ui)
├── hooks/
├── lib/                       # utilities, formatters, fetchers
├── services/                  # frontend service clients (auth, market, etc.)
├── store/                     # Zustand stores
├── providers/                 # context providers
├── styles/
├── types/                     # local-only types (shared → packages/types)
├── public/
├── tests/
├── package.json
├── tsconfig.json
├── tailwind.config.ts
└── next.config.ts
```

## FastAPI service (every service)

```
services/<name>/
├── app/
│   ├── api/                   # route handlers
│   │   └── v1/
│   ├── core/                  # config, logging, db setup
│   ├── middleware/
│   ├── dependencies/          # FastAPI dependencies (auth, db sessions)
│   ├── schemas/               # Pydantic models (request/response)
│   ├── models/                # SQLAlchemy models
│   ├── repositories/          # DB access layer
│   ├── services/              # business logic
│   ├── workers/               # background tasks
│   ├── clients/               # external API clients
│   ├── utils/
│   └── main.py
├── tests/
│   ├── unit/
│   ├── integration/
│   └── conftest.py
├── alembic/                   # migrations (if owns DB tables)
├── Dockerfile
├── pyproject.toml
└── README.md
```

### Layering rule

```
api/  →  services/  →  repositories/  →  models/
                  ↘  clients/  (external APIs)
```

API routes never call repositories or models directly. Always go through `services/`.

## Market data service specifics

```
services/market-data-service/app/
├── ingestion/                 # cron + on-demand ingestion
├── websocket/                 # WS connection manager
├── providers/                 # Polygon, Binance, yfinance, AlphaVantage
│   ├── base.py
│   ├── polygon_provider.py
│   ├── binance_provider.py
│   └── yfinance_provider.py
├── pipelines/
│   ├── ohlcv_pipeline.py
│   ├── news_pipeline.py
│   └── tick_pipeline.py
├── processors/                # normalization, dedup
└── storage/                   # TimescaleDB writes
```

## Prediction service specifics

```
services/prediction-service/app/
├── feature_engineering/
│   ├── technical_indicators.py
│   ├── market_features.py
│   ├── macro_features.py
│   └── sentiment_features.py
├── training/
│   ├── xgboost_trainer.py
│   ├── lgbm_trainer.py
│   └── transformer_trainer.py
├── inference/
├── pipelines/
├── registry/                  # MLflow integration
└── evaluation/
```

## Backtesting service specifics

```
services/backtesting-service/app/
├── engines/
│   └── vectorbt_engine.py
├── strategies/
│   ├── mean_reversion.py
│   ├── momentum.py
│   └── ml_strategy.py
├── metrics/
│   ├── sharpe.py
│   ├── drawdown.py
│   └── alpha_beta.py
├── execution/                 # simulated execution model
└── simulation/
```

## Agent service specifics

```
services/agent-service/app/
├── agents/
│   ├── research_agent.py
│   ├── risk_agent.py
│   ├── portfolio_agent.py
│   └── supervisor_agent.py
├── graphs/                    # LangGraph state machines
│   ├── research_graph.py
│   └── supervisor_graph.py
├── tools/
│   ├── market_tool.py
│   ├── portfolio_tool.py
│   ├── news_tool.py
│   └── analytics_tool.py
├── memory/
├── orchestration/
├── prompts/
├── retrieval/                 # RAG components
└── workflows/
```

## RL service specifics (Phase 8)

```
services/rl-service/app/
├── environments/
│   ├── single_asset_env.py
│   ├── portfolio_env.py
│   └── multi_agent_env.py
├── agents/
├── rewards/
├── trainers/
│   ├── ppo_trainer.py
│   ├── dqn_trainer.py
│   └── sac_trainer.py
├── evaluation/
└── replay/
checkpoints/                   # gitignored
experiments/                   # MLflow / W&B managed
```

## Shared packages

### `packages/ui/`
```
packages/ui/
├── src/
│   ├── components/
│   ├── layouts/
│   ├── charts/
│   ├── tables/
│   ├── hooks/
│   └── utils/
├── package.json
├── tsconfig.json
└── index.ts
```

### `packages/types/`
```
packages/types/
├── src/
│   ├── market.ts
│   ├── portfolio.ts
│   ├── signals.ts
│   ├── analytics.ts
│   ├── agents.ts
│   └── auth.ts
├── package.json
└── index.ts
```

### `packages/sdk/`
```
packages/sdk/
├── market/
├── portfolio/
├── prediction/
├── analytics/
├── agent/
└── auth/
```

Each sub-package has `client.ts`, `types.ts`, `queries.ts`, `mutations.ts`.

## AI directory (Python, importable by services)

```
ai/
├── agents/
├── models/
│   ├── financial_llm/
│   ├── sentiment_models/
│   └── forecast_models/
├── embeddings/
├── rag/
│   ├── ingestion/
│   ├── chunking/
│   ├── retrieval/
│   └── ranking/
├── experiments/
├── datasets/
├── evaluation/
└── prompts/
```

## Infra

```
infra/
├── docker/
├── kubernetes/                # Phase 11+
│   ├── base/
│   ├── staging/
│   └── production/
├── terraform/                 # Phase 11+
├── monitoring/                # Phase 11+
│   ├── prometheus/
│   ├── grafana/
│   └── loki/
├── nginx/
├── github-actions/            # workflow templates
└── scripts/
```

## Architecture invariants

**Every service has:**
- `app/api/` (routes)
- `app/services/` (business logic)
- `app/schemas/` (Pydantic)
- `app/models/` (SQLAlchemy if owns DB tables)
- `tests/`
- `Dockerfile`
- `pyproject.toml`

**Never mix:**
- ❌ API routes with ML logic
- ❌ UI state with API calls (use store + queries)
- ❌ RL logic with portfolio analytics
- ❌ AI prompts with orchestration code

## See also

- [`/new-service` command](../../.claude/commands/new-service.md)
- [Service topology](../architecture/03-service-topology.md)
