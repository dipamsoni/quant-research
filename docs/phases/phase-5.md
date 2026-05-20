# Phase 5 — Backtesting Platform

**Duration:** ~4 weeks
**Goal:** Strategy testing lab using vectorbt with proper metrics.

> Read [step-05 (Phase E: backtest validation)](../plan/step-05-quant-ml-roadmap.md) and [step-12](../plan/step-12-open-source-reuse.md).

## Acceptance criteria

- [ ] User can define a strategy via Python code or simple parameter UI
- [ ] Backtest runs against historical OHLCV with configurable costs
- [ ] Output: equity curve, drawdown chart, trade log, full metrics
- [ ] Metrics: Sharpe, Sortino, max drawdown, CAGR, win rate, profit factor, turnover
- [ ] User can compare multiple strategies side-by-side
- [ ] Backtests persisted; user can revisit prior runs

## Task list

### Week 1: Engine
- [ ] `services/backtesting-service/` scaffold
- [ ] Tables: `strategies`, `backtests`, `backtest_trades`, `backtest_metrics`
- [ ] Wrap vectorbt in `app/engines/vectorbt_engine.py`
- [ ] Built-in strategy templates:
  - SMA crossover
  - RSI mean reversion
  - Momentum
  - ML-signal-driven (uses Phase 4 signals)
- [ ] Configurable: initial capital, transaction cost (bps), slippage (bps)

### Week 2: API
- [ ] `POST /api/v1/backtesting/strategies` — save a strategy
- [ ] `POST /api/v1/backtesting/run` — async run a backtest
- [ ] `GET /api/v1/backtesting/results/{id}` — equity curve + metrics
- [ ] `GET /api/v1/backtesting/results/{id}/trades` — paginated trade log
- [ ] Background worker (Dramatiq or simple FastAPI background task) for runs

### Week 3: Metrics
- [ ] `app/metrics/sharpe.py`, `sortino.py`, `drawdown.py`, `alpha_beta.py`
- [ ] Per-trade analysis: avg win, avg loss, expectancy
- [ ] Rolling Sharpe, rolling drawdown
- [ ] Statistical significance: bootstrap or t-test on returns

### Week 4: Frontend
- [ ] `/backtesting` route: strategy builder + run interface
- [ ] Equity curve chart
- [ ] Drawdown chart (underwater plot)
- [ ] Metrics summary card
- [ ] Trade history table (virtualized)
- [ ] Comparison view: select 2–4 backtests, overlay equity curves
- [ ] Acceptance check; tag; advance

## Out of scope

- ❌ Live trading (out of MVP scope entirely)
- ❌ Walk-forward optimization (Phase 7+)
- ❌ Multi-asset portfolio backtests (Phase 7)

## Open-source

- **vectorbt** — primary engine
- **Backtrader** — alternative for event-driven, save for Phase 7+
- **scipy.stats** — significance tests

## Pitfalls

- **No transaction costs.** Default to 15 bps for NSE stocks (covers STT + brokerage), 10 bps for crypto. Show user the slider.
- **No slippage.** Default to 5 bps; more for low-liquidity.
- **Best-fit overfitting.** Show out-of-sample Sharpe separately from in-sample.
- **Ignoring drawdown periods.** A 30% Sharpe-2 strategy with 60% drawdown is not a good strategy.
- **Survivorship bias.** Use a proper universe (e.g., NSE 500 historical constituents) not just "current Nifty 500".
