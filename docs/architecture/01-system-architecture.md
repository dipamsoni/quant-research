# System Architecture

> Living document. Update as services come online.

## Current state (Phase 3)

```
┌──────────────┐     ┌────────────────┐     ┌─────────────────────┐     ┌────────────┐
│  Next.js     │────▶│  api-gateway   │────▶│  market-data :8001  │────▶│  Postgres  │
│  apps/web    │     │  :8000         │     │  portfolio   :8002  │     │  (TimescaleDB)│
└──────────────┘     └────────────────┘     └─────────────────────┘     ├────────────┤
                                                                          │  Redis :6379│
                                                                          └────────────┘
```

api-gateway proxies all frontend traffic. Each service owns its DB tables + Alembic migrations.

## Target state (Phase 11+)

See [step-01](../plan/step-01-foundation-architecture.md) and [step-09](../plan/step-09-deployment.md).

## Service boundaries

Even when running as a near-monolith in MVP, organize code by service:

```
services/
├── api-gateway/           # always its own process
├── market-data-service/   # standalone service (port 8001)
├── portfolio-service/     # standalone service (port 8002)
├── prediction-service/    # split out when ML inference latency matters
├── backtesting-service/   # split out when backtests block other work
├── agent-service/         # split out for separate scaling
├── analytics-service/     # split out in Phase 7+
├── rl-service/            # always separate (GPU)
└── notification-service/  # split out in Phase 7+
```

## Communication

- Phases 1-7: REST between services (or in-process function calls if monolithic)
- Phase 8+: Kafka for event streams
- Always: WebSockets for real-time UI

## Data ownership

| Service | Tables it owns |
|---------|----------------|
| api-gateway / auth | `users`, `sessions` |
| market-data | `assets`, `ohlcv_candles`, `news_articles`, `news_embeddings` |
| portfolio | `portfolios`, `holdings`, `transactions`, `portfolio_metrics` |
| prediction | `prediction_models`, `predictions`, `feature_store`, `trading_signals` |
| backtesting | `strategies`, `backtests`, `backtest_trades`, `backtest_metrics` |
| agent | `agent_conversations`, `agent_messages`, `research_reports` |
| rl | `rl_experiments`, `rl_training_runs`, `rl_actions` |
| analytics | `analytics_snapshots`, `realtime_metrics` |

Cross-service queries happen through APIs, never direct DB joins across service boundaries.

## See also
- [Database schema](02-database-schema.md)
- [Service topology](03-service-topology.md)
- [Deployment](09-deployment.md)
