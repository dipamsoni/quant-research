# Database Schema Reference

> Authoritative table definitions. Update as migrations land.

## Conventions

- All IDs are `UUID` (`gen_random_uuid()`)
- All `created_at` / `updated_at` are `TIMESTAMPTZ NOT NULL DEFAULT NOW()`
- All foreign keys have `ON DELETE` policies explicitly chosen
- Indexes follow `idx_<table>_<columns>` naming
- All tables have RLS-ready columns (`tenant_id` reserved for Phase 12)

## Phase 1 tables

### `users`
```sql
CREATE TABLE users (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email           CITEXT UNIQUE NOT NULL,
  username        CITEXT UNIQUE NOT NULL,
  hashed_password TEXT NOT NULL,
  full_name       TEXT,
  role            TEXT NOT NULL DEFAULT 'user',
  is_active       BOOLEAN NOT NULL DEFAULT TRUE,
  created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_users_email ON users (email);
```

### `sessions`
```sql
CREATE TABLE sessions (
  id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id           UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  refresh_token_hash TEXT NOT NULL,
  ip_address        INET,
  device_info       TEXT,
  expires_at        TIMESTAMPTZ NOT NULL,
  created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_sessions_user_id ON sessions (user_id);
```

## Phase 2 tables

### `assets`
```sql
CREATE TABLE assets (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  symbol      TEXT UNIQUE NOT NULL,
  name        TEXT NOT NULL,
  asset_type  TEXT NOT NULL,           -- 'stock' | 'crypto' | 'etf' | 'forex'
  exchange    TEXT NOT NULL,
  currency    TEXT NOT NULL,
  sector      TEXT,
  industry    TEXT,
  is_active   BOOLEAN NOT NULL DEFAULT TRUE,
  created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_assets_symbol ON assets (symbol);
CREATE INDEX idx_assets_type ON assets (asset_type);
```

### `ohlcv_candles` (TimescaleDB hypertable)
```sql
CREATE TABLE ohlcv_candles (
  time        TIMESTAMPTZ NOT NULL,
  asset_id    UUID NOT NULL REFERENCES assets(id) ON DELETE CASCADE,
  timeframe   TEXT NOT NULL,
  open        NUMERIC(20, 8) NOT NULL,
  high        NUMERIC(20, 8) NOT NULL,
  low         NUMERIC(20, 8) NOT NULL,
  close       NUMERIC(20, 8) NOT NULL,
  volume      NUMERIC(28, 8) NOT NULL,
  vwap        NUMERIC(20, 8),
  trade_count INTEGER,
  source      TEXT NOT NULL,
  PRIMARY KEY (time, asset_id, timeframe)
);
SELECT create_hypertable('ohlcv_candles', 'time');
ALTER TABLE ohlcv_candles SET (
  timescaledb.compress,
  timescaledb.compress_segmentby = 'asset_id, timeframe'
);
SELECT add_compression_policy('ohlcv_candles', INTERVAL '7 days');
CREATE INDEX idx_candles_asset_time ON ohlcv_candles (asset_id, time DESC);
```

### `news_articles`
```sql
CREATE TABLE news_articles (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  title           TEXT NOT NULL,
  content         TEXT,
  source          TEXT NOT NULL,
  url             TEXT NOT NULL,
  published_at    TIMESTAMPTZ NOT NULL,
  sentiment_score NUMERIC(5, 4),
  symbols         TEXT[],
  created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_news_published ON news_articles (published_at DESC);
CREATE INDEX idx_news_symbols ON news_articles USING GIN (symbols);
```

## Phase 3 tables

### `portfolios`
```sql
CREATE TABLE portfolios (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id       UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  name          TEXT NOT NULL,
  base_currency TEXT NOT NULL DEFAULT 'INR',
  risk_profile  TEXT,
  created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

### `holdings`
```sql
CREATE TABLE holdings (
  id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  portfolio_id UUID NOT NULL REFERENCES portfolios(id) ON DELETE CASCADE,
  asset_id     UUID NOT NULL REFERENCES assets(id),
  quantity     NUMERIC(28, 8) NOT NULL,
  avg_price    NUMERIC(20, 8) NOT NULL,
  market_value NUMERIC(28, 8),
  updated_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE (portfolio_id, asset_id)
);
```

### `transactions`
```sql
CREATE TABLE transactions (
  id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  portfolio_id     UUID NOT NULL REFERENCES portfolios(id) ON DELETE CASCADE,
  asset_id         UUID NOT NULL REFERENCES assets(id),
  transaction_type TEXT NOT NULL,
  quantity         NUMERIC(28, 8) NOT NULL,
  price            NUMERIC(20, 8) NOT NULL,
  fees             NUMERIC(20, 8) NOT NULL DEFAULT 0,
  executed_at      TIMESTAMPTZ NOT NULL,
  created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_tx_portfolio ON transactions (portfolio_id);
CREATE INDEX idx_tx_executed ON transactions (executed_at DESC);
```

### `portfolio_metrics`
```sql
CREATE TABLE portfolio_metrics (
  id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  portfolio_id UUID NOT NULL REFERENCES portfolios(id) ON DELETE CASCADE,
  date         DATE NOT NULL,
  total_value  NUMERIC(28, 8) NOT NULL,
  daily_return NUMERIC(10, 8),
  sharpe_ratio NUMERIC(10, 4),
  max_drawdown NUMERIC(10, 8),
  volatility   NUMERIC(10, 8),
  beta         NUMERIC(10, 6),
  alpha        NUMERIC(10, 8),
  UNIQUE (portfolio_id, date)
);
```

## Phase 4+ tables

See [step-02 plan doc](../plan/step-02-database-schema.md) for `prediction_models`, `predictions`, `trading_signals`, `feature_store`, `strategies`, `backtests`, etc. Add to this file as you build them.

## Phase 6+ tables

```sql
-- pgvector extension required
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE news_embeddings (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  article_id  UUID NOT NULL REFERENCES news_articles(id) ON DELETE CASCADE,
  embedding   VECTOR(1536) NOT NULL,
  created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX ON news_embeddings USING ivfflat (embedding vector_cosine_ops);
```

## Migrations

All schema changes via Alembic. Never `ALTER TABLE` by hand on staging or production.

```bash
cd services/<service>
alembic revision --autogenerate -m "describe change"
alembic upgrade head
```
