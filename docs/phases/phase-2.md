# Phase 2 — Market Data Platform

**Duration:** ~4 weeks
**Goal:** Real-time market data, candlestick charts, watchlists, WebSocket streaming.

> Read [step-01](../plan/step-01-foundation-architecture.md), [step-02](../plan/step-02-database-schema.md), and [step-08](../plan/step-08-ui-wireframes.md) before starting.

## Acceptance criteria

- [ ] User can search for any of ~5000 stocks/crypto by symbol or name
- [ ] User sees live candlestick charts with multiple timeframes (1m, 5m, 1h, 1d)
- [ ] Charts have toggleable indicators: SMA, EMA, RSI, MACD, Bollinger Bands
- [ ] User can build a watchlist; live prices update via WebSocket
- [ ] OHLCV history stored in TimescaleDB with at least 2 years of daily data per asset
- [ ] WebSocket disconnects/reconnects gracefully on network changes
- [ ] News feed visible per asset (last 24h headlines)
- [ ] All endpoints documented in OpenAPI

## Task list

### Week 1: Data ingestion

#### 2.1 Market data service scaffold
- [ ] `services/market-data-service/` with the standard FastAPI layout
- [ ] Tables: `assets`, `ohlcv_candles` (TimescaleDB hypertable), `news_articles`
- [ ] Alembic migration including `CREATE EXTENSION IF NOT EXISTS timescaledb;` and `SELECT create_hypertable('ohlcv_candles', 'time');`
- [ ] Compression policy: `ALTER TABLE ohlcv_candles SET (timescaledb.compress, timescaledb.compress_segmentby = 'asset_id');`
- [ ] Indexes: `(asset_id, time DESC)`, `(timeframe)`

#### 2.2 Data providers
- [ ] `app/providers/base.py` — abstract `MarketDataProvider`
- [ ] `app/providers/yfinance_provider.py` — historical daily data (free, no API key)
- [ ] `app/providers/alphavantage_provider.py` — intraday data (free tier)
- [ ] `app/providers/polygon_provider.py` — real-time + historical (paid; gate behind env flag)
- [ ] `app/providers/binance_provider.py` — crypto OHLCV + WS
- [ ] Adapter pattern: each provider returns normalized `OHLCVCandle` Pydantic model

#### 2.3 Ingestion pipelines
- [ ] `app/pipelines/ohlcv_pipeline.py` — backfill historical candles for an asset
- [ ] `app/pipelines/realtime_pipeline.py` — connect to provider WS, write live candles
- [ ] Background scheduler (APScheduler or simple asyncio task) to refresh daily data nightly
- [ ] Deduplication via primary key `(time, asset_id, timeframe)`
- [ ] Symbol seeding: import top 500 US stocks + top 50 crypto from a static list

### Week 2: API + WebSocket

#### 2.4 REST endpoints
- [ ] `GET /api/v1/market/assets?search=&type=` — paginated list
- [ ] `GET /api/v1/market/assets/{symbol}` — asset details
- [ ] `GET /api/v1/market/candles?symbol=&timeframe=&start=&end=` — historical OHLCV
- [ ] `GET /api/v1/market/price/{symbol}` — latest price (cached in Redis, 5s TTL)
- [ ] `GET /api/v1/market/news?symbol=` — news headlines

#### 2.5 WebSocket gateway
- [ ] `WS /ws/prices?symbols=AAPL,TSLA,BTCUSDT`
- [ ] Connection manager (per-client subscription tracking)
- [ ] On price update: broadcast to subscribed clients only
- [ ] Heartbeat every 30s; close stale connections
- [ ] Reconnection-friendly: client sends sequence number, server replays missed
- [ ] Auth via JWT on WS handshake

#### 2.6 News ingestion
- [ ] Provider: Finnhub (free tier) or NewsAPI
- [ ] Periodic ingestion task (every 10 min)
- [ ] Store in `news_articles` with `published_at`, `source`, `url`, raw `content`

### Week 3: Frontend market terminal

#### 2.7 Watchlist UI
- [ ] `apps/web/app/(dashboard)/market/page.tsx` — main market view
- [ ] Sidebar watchlist with add/remove
- [ ] Watchlist persisted per-user via API (`GET/POST/DELETE /api/v1/market/watchlist`)
- [ ] Live price column updates via WebSocket subscription

#### 2.8 Candlestick chart
- [ ] Install `lightweight-charts` in `apps/web`
- [ ] `components/charts/CandlestickChart.tsx` — wrapped TradingView Lightweight Charts
- [ ] Timeframe toggle: 1m, 5m, 1h, 1d, 1w
- [ ] Indicator toggles: SMA(20), EMA(50), RSI(14), MACD(12,26,9), Bollinger(20,2)
- [ ] Use `pandas-ta` server-side or compute indicators on backend; do not compute in browser
- [ ] Volume bars below price
- [ ] Crosshair with OHLC tooltip

#### 2.9 News panel
- [ ] `components/market/NewsPanel.tsx` — list of headlines for selected asset
- [ ] Click headline → opens source in new tab
- [ ] Updates when selected symbol changes

### Week 4: Polish + reliability

#### 2.10 Reliability
- [ ] Provider failover: if Polygon down, fall back to yfinance
- [ ] Rate limiting per provider (respect free-tier limits)
- [ ] Error handling: gaps in OHLCV data flagged, not silently ignored
- [ ] Tests: unit tests for each provider adapter, integration test for full ingestion flow

#### 2.11 Performance
- [ ] Cache asset list in Redis (refresh hourly)
- [ ] WebSocket throttling: coalesce price updates per 100ms (don't spam UI)
- [ ] Use `react-window` or TanStack Virtual for large watchlist tables

#### 2.12 Acceptance check
- [ ] Run through every item in "Acceptance criteria"
- [ ] Tag: `git tag phase-2-complete`
- [ ] Update `docs/CURRENT_PHASE.md`

## Out of scope

- ❌ Order book / Level 2 data (advanced, Phase 10+)
- ❌ Tick data storage (Phase 10+)
- ❌ Portfolio (Phase 3)
- ❌ Predictions (Phase 4)

## Open-source to use

- **TradingView Lightweight Charts** for charts
- **pandas-ta** for indicators
- **yfinance** for free historical
- **TimescaleDB** for the OHLCV hypertable

## Common pitfalls

- **Provider API keys in code.** Use env vars only.
- **Storing OHLCV in regular Postgres tables.** Always TimescaleDB hypertable for time-series.
- **Computing indicators in the browser.** Always server-side; cache results.
- **No gap detection.** If you ingest 6 months of data with a 2-day gap nobody notices, it'll silently break ML training later.
- **WS without auth.** Anyone can subscribe to anyone's stream — bad for production.
