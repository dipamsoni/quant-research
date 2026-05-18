# Phase 7 — Portfolio Optimization

**Duration:** ~4 weeks
**Goal:** Mean-variance, risk parity, Black-Litterman optimization with risk constraints.

> Read [step-12 (PyPortfolioOpt)](../plan/step-12-open-source-reuse.md). Only start after MVP has real users.

## Acceptance criteria
- [ ] User can request optimized weights for a portfolio of N assets
- [ ] At least 3 methods: mean-variance, risk parity, Black-Litterman
- [ ] User-specified constraints: max position size, sector limits, min cash
- [ ] Efficient frontier visualization
- [ ] Compare current vs optimized allocation side-by-side
- [ ] Rebalancing suggestions with estimated cost

## Task list

### Week 1: Engine
- [ ] `services/analytics-service/` (or extend portfolio-service)
- [ ] Install PyPortfolioOpt, cvxpy
- [ ] `app/optimization/efficient_frontier.py` — mean-variance
- [ ] `app/optimization/risk_parity.py`
- [ ] `app/optimization/black_litterman.py`
- [ ] Risk constraints: max weight, sector caps, leverage limit

### Week 2: API
- [ ] `POST /api/v1/portfolio/{id}/optimize` — accepts method + constraints, returns weights
- [ ] `GET /api/v1/portfolio/{id}/efficient-frontier` — points along the frontier

### Week 3: Frontend
- [ ] `/portfolio/optimize` page
- [ ] Method selector
- [ ] Constraint inputs
- [ ] Efficient frontier chart (ECharts)
- [ ] Side-by-side: current allocation vs optimized
- [ ] Rebalance preview: trades needed + estimated cost

### Week 4: Risk analytics
- [ ] VaR calculations (historical + parametric)
- [ ] CVaR (expected shortfall)
- [ ] Stress testing scenarios (2008, 2020 COVID, custom)
- [ ] Risk dashboard component

## Out of scope
- ❌ Live execution
- ❌ Tax-aware optimization (advanced)
- ❌ Multi-period optimization

## Pitfalls
- **Garbage in, garbage out.** Mean-variance is highly sensitive to expected return estimates. Use shrinkage estimators or Black-Litterman with priors.
- **Over-concentrated solutions.** Add max-weight constraints by default (e.g., 25% per name).
- **Ignoring transaction costs in rebalance.** Quote estimated costs; let users skip small trades.
