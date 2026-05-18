# Phase 3 — Portfolio + Analytics

**Duration:** ~4 weeks
**Goal:** Working portfolio tracker with real PnL, allocation, and risk metrics.

> Read [step-02 (portfolio tables)](../plan/step-02-database-schema.md) and [step-08](../plan/step-08-ui-wireframes.md).

## Acceptance criteria

- [ ] User can create multiple portfolios
- [ ] User can record buy/sell transactions
- [ ] System computes: total value, cost basis, unrealized PnL, realized PnL, daily return
- [ ] System computes risk metrics: Sharpe ratio, max drawdown, volatility, beta vs SPY
- [ ] Allocation pie chart by asset and sector
- [ ] Performance line chart vs benchmark (SPY)
- [ ] Holdings table is sortable, virtualized, exportable to CSV

## Task list

### Week 1: Service + schema
- [ ] `services/portfolio-service/` scaffold (or as a router in api-gateway for MVP)
- [ ] Tables: `portfolios`, `holdings`, `transactions`, `portfolio_metrics`
- [ ] Alembic migration

### Week 2: Business logic
- [ ] `app/services/portfolio.py` — CRUD on portfolios
- [ ] `app/services/transactions.py` — record buy/sell, recompute holdings
- [ ] `app/services/metrics.py` — Sharpe, drawdown, volatility, beta, alpha
- [ ] Use `numpy` + `pandas`; price history fetched via market-data SDK
- [ ] Daily snapshot job: compute and store portfolio_metrics each day

### Week 3: API + endpoints
- [ ] `POST /api/v1/portfolio` create
- [ ] `GET /api/v1/portfolio` list user's portfolios
- [ ] `GET /api/v1/portfolio/{id}` full details
- [ ] `POST /api/v1/portfolio/{id}/transactions` record buy/sell
- [ ] `GET /api/v1/portfolio/{id}/metrics` time-series of metrics
- [ ] `GET /api/v1/portfolio/{id}/allocation` pie chart data

### Week 4: Frontend
- [ ] `/portfolio` route with portfolio selector
- [ ] Summary cards (total value, daily return, Sharpe, drawdown, cash)
- [ ] Allocation pie chart (Tremor or Recharts)
- [ ] Performance line chart (Recharts) vs SPY
- [ ] Holdings table (TanStack Table with virtualization)
- [ ] Add transaction modal
- [ ] CSV export
- [ ] Live updates via WebSocket subscription to held symbols

## Out of scope

- ❌ Optimization (Phase 7)
- ❌ Order placement (no live trading; we record manually)
- ❌ Tax-lot accounting (advanced, Phase 12+ if ever)

## Common pitfalls

- **Wrong PnL on shorts.** Make sure your formula handles negative quantity correctly.
- **Beta computed against wrong benchmark.** Use SPY consistently; let users override later.
- **Metrics computed in API request.** Move to background job; cache in `portfolio_metrics`.
- **Stale prices.** Use the latest price from market-data, not a stale snapshot.
