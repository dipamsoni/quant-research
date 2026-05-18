# Step 4 — Exact APIs to Build

> Reference doc. Detailed contracts in [architecture/04-api-contracts.md](../architecture/04-api-contracts.md).

## Versioning

All routes prefixed with `/api/v1/`. Never break existing clients — add `/api/v2/` instead.

## Standard response envelope

```json
// Success
{ "success": true, "data": {} }

// Error
{ "error": { "code": "INVALID_SYMBOL", "message": "...", "details": {} } }
```

## Pagination (cursor-based)

```json
{
  "data": [],
  "pagination": { "next_cursor": "abc123", "has_more": true }
}
```

## Routes by phase

### Phase 1: Auth
```
POST   /api/v1/auth/register
POST   /api/v1/auth/login
POST   /api/v1/auth/refresh
POST   /api/v1/auth/logout
GET    /api/v1/auth/me
```

### Phase 2: Market data
```
GET    /api/v1/market/assets             ?page&limit&asset_type&search
GET    /api/v1/market/assets/{symbol}
GET    /api/v1/market/candles            ?symbol&timeframe&start&end
GET    /api/v1/market/price/{symbol}
GET    /api/v1/market/news               ?symbol
WS     /ws/prices                        ?symbols=AAPL,TSLA
```

### Phase 3: Portfolio
```
POST   /api/v1/portfolio
GET    /api/v1/portfolio
GET    /api/v1/portfolio/{id}
POST   /api/v1/portfolio/{id}/positions
GET    /api/v1/portfolio/{id}/metrics
```

### Phase 4: ML / Predictions
```
POST   /api/v1/ml/predict-price
POST   /api/v1/ml/train               (admin)
GET    /api/v1/ml/models
GET    /api/v1/ml/features/{symbol}
POST   /api/v1/signals/generate
GET    /api/v1/signals
```

### Phase 5: Backtesting
```
POST   /api/v1/backtesting/strategies
POST   /api/v1/backtesting/run
GET    /api/v1/backtesting/results/{backtest_id}
```

### Phase 6: Agents
```
POST   /api/v1/agents/chat
POST   /api/v1/agents/research
GET    /api/v1/agents/tasks
```

### Phase 7: Optimization
```
POST   /api/v1/portfolio/{id}/optimize
GET    /api/v1/analytics/dashboard
GET    /api/v1/analytics/risk
```

### Phase 8+: RL & multi-agent
```
POST   /api/v1/rl/experiments
POST   /api/v1/rl/train
GET    /api/v1/rl/metrics/{experiment_id}
POST   /api/v1/agents/workflow
```

## WebSocket channels

```
/ws/prices       — live price ticks
/ws/portfolio    — portfolio value updates
/ws/signals      — new trading signals
/ws/agents       — agent reasoning stream (Phase 6+)
/ws/analytics    — dashboard metrics (Phase 7+)
```

## Rate limits

| Endpoint type | Limit |
|---------------|-------|
| Public | 100/min |
| Authenticated | 1000/min |
| Trading | 50/min |
| AI | 20/min |

## OpenAPI

FastAPI auto-generates `/docs`, `/redoc`, `/openapi.json`. Use these as the source of truth for the frontend SDK.

## See also

- [API contracts](../architecture/04-api-contracts.md) — exact request/response schemas
