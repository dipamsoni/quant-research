# API Contracts

> Source of truth for request/response shapes. The OpenAPI spec at `/docs` is authoritative — this file is a quick reference.

## Conventions

- All routes under `/api/v1/`
- All responses wrap data: `{ "success": true, "data": {...} }` or `{ "error": {...} }`
- Pagination is cursor-based: `?cursor=<opaque>&limit=50`
- Timestamps are ISO-8601 in UTC
- IDs are UUIDs

## Auth (Phase 1)

### POST /api/v1/auth/register
```json
// Request
{ "email": "user@example.com", "username": "alice", "password": "...", "full_name": "Alice" }

// 201 Response
{
  "success": true,
  "data": {
    "user": { "id": "...", "email": "...", "username": "...", "full_name": "...", "role": "user" },
    "access_token": "...",
    "refresh_token": "...",
    "expires_in": 900
  }
}
```

### POST /api/v1/auth/login
```json
// Request
{ "email": "...", "password": "..." }
// Response: same as register
```

### POST /api/v1/auth/refresh
```json
{ "refresh_token": "..." }
// Returns new access + refresh
```

### POST /api/v1/auth/logout
Headers: `Authorization: Bearer <access>`. Revokes session.

### GET /api/v1/auth/me
Headers: `Authorization: Bearer <access>`.
```json
{ "success": true, "data": { "id": "...", "email": "...", "username": "...", "role": "user" } }
```

## Market data (Phase 2)

### GET /api/v1/market/assets
Query: `search`, `asset_type`, `cursor`, `limit`
```json
{
  "success": true,
  "data": [{ "id": "...", "symbol": "AAPL", "name": "Apple Inc.", "asset_type": "stock", "exchange": "NASDAQ" }],
  "pagination": { "next_cursor": "...", "has_more": true }
}
```

### GET /api/v1/market/assets/{symbol}
Returns full asset including current price.

### GET /api/v1/market/candles
Query: `symbol`, `timeframe` (1m|5m|1h|1d|1w), `start`, `end`
```json
{
  "success": true,
  "data": [
    { "time": "2026-05-10T15:30:00Z", "open": 220.0, "high": 221.5, "low": 219.8, "close": 220.7, "volume": 1234567 }
  ]
}
```

### GET /api/v1/market/price/{symbol}
```json
{ "success": true, "data": { "symbol": "AAPL", "price": 220.45, "as_of": "..." } }
```

### GET /api/v1/market/news?symbol=AAPL
```json
{
  "success": true,
  "data": [
    { "id": "...", "title": "...", "source": "Reuters", "url": "...", "published_at": "...", "sentiment_score": 0.42 }
  ]
}
```

### WS /ws/prices?symbols=AAPL,TSLA
- Auth via `Authorization` header on handshake (or `?token=` query if browser limitations)
- Server pushes:
  ```json
  { "type": "tick", "symbol": "AAPL", "price": 220.45, "ts": "..." }
  ```
- Heartbeat: server sends `{"type":"ping"}` every 30s; client replies `{"type":"pong"}`

## Portfolio (Phase 3)

### POST /api/v1/portfolio
```json
// Request
{ "name": "Long Term", "base_currency": "USD", "risk_profile": "moderate" }
```

### GET /api/v1/portfolio
List user's portfolios.

### GET /api/v1/portfolio/{id}
Includes holdings, current value, recent metrics.

### POST /api/v1/portfolio/{id}/transactions
```json
{
  "asset_id": "...",
  "transaction_type": "BUY",
  "quantity": 10,
  "price": 220.45,
  "fees": 1.0,
  "executed_at": "2026-05-10T15:30:00Z"
}
```

### GET /api/v1/portfolio/{id}/metrics?from=&to=
Time series of metrics.

### GET /api/v1/portfolio/{id}/allocation
Current allocation breakdown.

## ML / Predictions (Phase 4)

### POST /api/v1/ml/predict-price
```json
// Request
{ "symbol": "AAPL", "horizon_days": 1 }

// Response
{
  "success": true,
  "data": {
    "symbol": "AAPL",
    "predicted_return": 0.012,
    "confidence": 0.71,
    "model": "next_day_return_xgb_v1",
    "as_of": "..."
  }
}
```

### GET /api/v1/signals?symbol=&since=
```json
{
  "success": true,
  "data": [
    { "id": "...", "symbol": "AAPL", "action": "BUY", "confidence": 0.78, "target_return": 0.015, "generated_at": "..." }
  ]
}
```

## Backtesting (Phase 5)

### POST /api/v1/backtesting/run
```json
// Request
{
  "strategy_id": "...",   // or inline:
  "strategy_code": "...",
  "symbols": ["AAPL", "MSFT"],
  "start": "2024-01-01",
  "end": "2026-01-01",
  "initial_capital": 100000,
  "transaction_cost_bps": 5,
  "slippage_bps": 5
}

// 202 Accepted
{ "success": true, "data": { "backtest_id": "...", "status": "queued" } }
```

### GET /api/v1/backtesting/results/{id}
```json
{
  "success": true,
  "data": {
    "status": "completed",
    "metrics": {
      "sharpe": 1.42,
      "sortino": 1.81,
      "max_drawdown": 0.18,
      "cagr": 0.21,
      "win_rate": 0.54,
      "profit_factor": 1.6,
      "total_trades": 248
    },
    "equity_curve": [{ "date": "...", "value": 100000 }, ...]
  }
}
```

## Agents (Phase 6)

### POST /api/v1/agents/chat
Streaming response (SSE).
```json
// Request
{ "conversation_id": "...|null", "message": "What's driving AAPL today?" }

// Streamed events:
event: token       data: "Apple"
event: tool_call   data: { "tool": "news_tool.search", "args": {...} }
event: tool_result data: { "results": [...] }
event: token       data: " is up..."
event: citation    data: { "source": "Reuters", "url": "..." }
event: done        data: { "conversation_id": "..." }
```

### GET /api/v1/agents/conversations
List user's conversations.

### GET /api/v1/agents/conversations/{id}
Full message history with citations.

## Errors

Standard envelope:
```json
{
  "error": {
    "code": "INVALID_SYMBOL",
    "message": "Symbol XYZ not found",
    "details": { "symbol": "XYZ" }
  }
}
```

Common codes:
- `UNAUTHORIZED` (401)
- `FORBIDDEN` (403)
- `NOT_FOUND` (404)
- `VALIDATION_ERROR` (422)
- `RATE_LIMITED` (429)
- `INTERNAL_ERROR` (500)

## Versioning

Never break v1. Add v2 routes for breaking changes; deprecate v1 with a sunset header:
```
Sunset: Sat, 31 Dec 2026 23:59:59 GMT
Deprecation: true
Link: </api/v2/...>; rel="successor-version"
```
