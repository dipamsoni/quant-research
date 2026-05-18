# Step 2 — Complete Database Schema Design

> Reference doc. The full schema deep-dive lives in [architecture/02-database-schema.md](../architecture/02-database-schema.md).

## Database strategy

| Purpose | Technology |
|---------|------------|
| Relational data | PostgreSQL 16 |
| Time-series market data | TimescaleDB (extension on Postgres) |
| Caching | Redis 7 |
| Vector search | pgvector (extension on Postgres) |
| Object storage | MinIO/S3 (later) |

## Service-owned tables

Each microservice owns its own tables. Don't cross-query other services' tables — go through their API.

| Service | Owns |
|---------|------|
| auth-service | `users`, `sessions`, `api_keys` |
| market-data-service | `assets`, `ohlcv_candles`, `tick_data`, `news_articles`, `news_embeddings` |
| portfolio-service | `portfolios`, `holdings`, `transactions`, `portfolio_metrics` |
| prediction-service | `prediction_models`, `predictions`, `trading_signals`, `feature_store` |
| backtesting-service | `strategies`, `backtests`, `backtest_trades`, `backtest_metrics` |
| rl-service (later) | `rl_experiments`, `rl_training_runs`, `rl_actions` |
| agent-service (later) | `ai_agents`, `agent_conversations`, `research_reports`, `agent_tasks` |
| analytics-service (later) | `analytics_snapshots`, `realtime_metrics` |
| (shared) | `audit_logs`, `system_events` |

## Key design rules

1. **Don't mix transactional and analytical data.** User accounts ≠ tick data.
2. **Use TimescaleDB hypertables for OHLCV.** Convert with `SELECT create_hypertable('ohlcv_candles', 'time')`.
3. **Use pgvector for embeddings.** Don't add Qdrant unless you actually need it.
4. **Index aggressively on time-series queries.** `INDEX(asset_id, time DESC)` is the workhorse.
5. **JSONB for flexible analytics snapshots.** Don't over-normalize dashboard payloads.

## Critical tables (MVP)

### `users` (Phase 1)
```
id (UUID), email, username, hashed_password,
full_name, role, is_active, created_at, updated_at
```

### `assets` (Phase 2)
```
id, symbol, name, asset_type, exchange,
currency, sector, industry, is_active, created_at
```

### `ohlcv_candles` (Phase 2, TimescaleDB hypertable)
```
time, asset_id, timeframe, open, high, low, close,
volume, vwap, trade_count, source
PRIMARY KEY (time, asset_id, timeframe)
```

### `portfolios` (Phase 3)
```
id, user_id, name, base_currency, risk_profile, created_at
```

### `holdings` (Phase 3)
```
id, portfolio_id, asset_id, quantity, avg_price,
market_value, updated_at
```

### `transactions` (Phase 3)
```
id, portfolio_id, asset_id, transaction_type (BUY/SELL),
quantity, price, fees, executed_at
```

### `prediction_models` + `predictions` (Phase 4)

### `strategies` + `backtests` + `backtest_trades` (Phase 5)

### `news_embeddings` (Phase 6, pgvector)
```
id, article_id, embedding VECTOR(1536), created_at
```

## Indexes you'll need

- `INDEX(asset_id, time DESC)` on `ohlcv_candles`
- `INDEX(portfolio_id)` and `INDEX(executed_at DESC)` on `transactions`
- `INDEX(asset_id, prediction_time)` on `predictions`
- `USING ivfflat (embedding vector_cosine_ops)` on embedding tables

## Don't build during MVP

- Event store / event sourcing tables (Phase 11+)
- RL training tables (Phase 8)
- Agent conversation tables (Phase 6+, but minimal)
- Multi-tenant isolation (Phase 12+)

## See also

- [Architecture deep-dive: schema](../architecture/02-database-schema.md)
- [Phase 1: bootstrap users + auth tables](../phases/phase-1.md)
- [Phase 2: market data tables + TimescaleDB](../phases/phase-2.md)
