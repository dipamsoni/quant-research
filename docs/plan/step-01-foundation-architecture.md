# Step 1 — Foundation System Architecture

> Reference doc. Read when implementing Phase 1 or making top-level architectural decisions.

## Architecture style

**Modular microservice architecture** — not a monolith, not random FastAPI routes, not disconnected ML notebooks.

```
                    ┌─────────────────────┐
                    │     Next.js App     │
                    │  Institutional UI   │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │     API Gateway     │
                    │      FastAPI        │
                    └──────────┬──────────┘
                               │
        ┌──────────────────────┼──────────────────────┐
        ▼                      ▼                      ▼
┌───────────────┐    ┌────────────────┐    ┌────────────────┐
│ Market Data   │    │ AI/ML Services │    │ Trading Engine │
└──────┬────────┘    └──────┬─────────┘    └──────┬─────────┘
       │                    │                     │
       └────────────────────┼─────────────────────┘
                            ▼
                 ┌─────────────────────┐
                 │ Shared Data Layer   │
                 │ Postgres + TimescaleDB
                 │ Redis + pgvector    │
                 └─────────────────────┘
```

## Core services (order to build them)

1. **api-gateway** — auth, rate limiting, routing, websockets
2. **market-data-service** — OHLCV, news, ingestion → TimescaleDB
3. **portfolio-service** — holdings, transactions, metrics
4. **prediction-service** — ML inference (XGBoost first)
5. **backtesting-service** — vectorbt-based strategy simulation
6. **agent-service** — LangGraph-based AI orchestration
7. **analytics-service** — dashboards, factor analysis (later)
8. **rl-service** — reinforcement learning (much later, Phase 8+)

## Tech stack (locked for MVP)

| Layer | Tech |
|-------|------|
| Frontend | Next.js 15, TypeScript, Tailwind, shadcn/ui, Zustand, React Query |
| Charts | TradingView Lightweight Charts + ECharts |
| Backend | FastAPI, Pydantic, SQLAlchemy, asyncio |
| DB | PostgreSQL 16 + TimescaleDB extension |
| Cache | Redis 7 |
| Vector | pgvector (NOT Qdrant for MVP) |
| ML | XGBoost, LightGBM, vectorbt, PyPortfolioOpt |
| AI | LangGraph, LlamaIndex |
| Containers | Docker + Docker Compose (k8s only at Phase 11+) |

## Communication style

- **Synchronous (REST):** auth, dashboard fetches, CRUD — use this for MVP
- **Asynchronous (Kafka/Redis Streams):** market streams, AI workflows, RL events — Phase 8+

## Build order (do not deviate)

```
Foundation (Phase 1)
    ↓
Data Layer (Phase 2)
    ↓
Prediction (Phase 4)
    ↓
Backtesting (Phase 5)
    ↓
Portfolio Optimization (Phase 7)
    ↓
RL (Phase 8)
    ↓
Multi-Agent (Phase 9)
```

**Common failure mode:** starting with RL or multi-agent systems first. Don't.

## See also

- [Phase 1 tasks](../phases/phase-1.md)
- [System architecture deep-dive](../architecture/01-system-architecture.md)
