# Open-Source Reuse Strategy

> See [step-12](../plan/step-12-open-source-reuse.md) for the full strategic doc.

## The rule

Reuse mature libraries for primitives. Build the product layer (UX, workflows, orchestration) yourself. Wrap external libs in adapters so you can swap them.

## Quick reference

### Frontend
- `lightweight-charts` — candlestick (Phase 2)
- `shadcn/ui` — components (Phase 1)
- `tremor` — KPI cards (Phase 3+)
- `echarts-for-react` — analytics charts (Phase 7+)
- `cmdk` — command palette (Phase 3+)
- `@tanstack/react-query` — server state
- `@tanstack/react-table` — tables
- `@tanstack/react-virtual` — virtualization
- `zustand` — client state
- `framer-motion` — animation (sparingly)

### Backend
- `fastapi` — web framework
- `pydantic` — validation
- `sqlalchemy` (async) — ORM
- `alembic` — migrations
- `asyncpg` — Postgres driver
- `redis-py` — Redis client
- `python-jose` + `passlib[bcrypt]` — auth
- `httpx` — HTTP client (over `requests`)
- `slowapi` — rate limiting

### Quant / ML
- `pandas-ta` — technical indicators (Phase 2)
- `xgboost` — primary model (Phase 4)
- `lightgbm` — alt model
- `mlflow` — registry + tracking (Phase 4+)
- `vectorbt` — backtesting (Phase 5)
- `pyportfolioopt` — optimization (Phase 7)
- `optuna` — hyperparameter search

### RL (Phase 8)
- `gymnasium` — env standard
- `stable-baselines3` — PPO, DQN, SAC
- `wandb` — experiment tracking
- `finrl` — reference implementations
- `ray[rllib]` — distributed / multi-agent (Phase 9)

### AI agents
- `langgraph` — orchestration (Phase 6)
- `langchain` — primitives (used via langgraph)
- `llama-index` — RAG, retrievers (Phase 6)
- `pgvector` extension + `pgvector` client — embeddings (Phase 6)
- `crewai` — quick prototyping (Phase 9, optional)

### Data infra
- TimescaleDB extension (Phase 2)
- pgvector extension (Phase 6)
- Redpanda or Kafka (Phase 8+)
- Dagster (Phase 11+, if you need orchestration)

### DevOps
- Docker + Docker Compose (Phase 1)
- GitHub Actions (Phase 1)
- Helm + Kustomize (Phase 11)
- Terraform (Phase 11)
- ArgoCD (Phase 11)

## Adapter pattern (mandatory for swappable libs)

Every external library that's load-bearing gets an adapter:

```
adapters/
├── vectorbt/
│   ├── __init__.py
│   ├── engine.py      # exposes our interface, calls vectorbt internally
│   └── types.py
├── finrl/
├── langgraph/
└── lightweight_charts/  (frontend, in TS)
```

Why: when (not if) one of these libraries gets abandoned, you swap one adapter, not 200 call sites.

## Vetting checklist before adding a dependency

- [ ] Last commit within 6 months?
- [ ] Issues actively triaged?
- [ ] License compatible (MIT, Apache 2.0, BSD)?
- [ ] No catastrophic CVEs in last 2 years?
- [ ] Sufficient documentation?
- [ ] Permissive enough to fork if needed?
- [ ] Reasonable bundle/install size?

If 2+ fail, look for an alternative.

## Don't use

- ❌ **Zipline** — abandoned
- ❌ **Quantopian-era frameworks** — most are dead
- ❌ Random crypto bots (they ship vulns)
- ❌ AutoGen for production agent workflows (LangGraph is better-supported)

## Study but don't fork

- **QuantConnect Lean** — read for design patterns, don't import
- **NautilusTrader** — institutional reference
- **OpenBB** — quant terminal patterns
- **Hummingbot** — execution patterns

## When to write your own

- The library doesn't exist for your specific need
- Existing libs are 10x more complex than what you need
- The library is unmaintained AND critical to a hot path
- You need IP / differentiation in this layer

NOT good reasons:
- "I want to learn"
- "It's more fun"
- "Their API is ugly"
