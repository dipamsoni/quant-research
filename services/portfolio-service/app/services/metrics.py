"""Portfolio metrics computation.

Two-layer design:
  - Pure functions (prefix _): numpy/pandas math, no I/O, fully unit-testable.
  - compute_all_metrics(): public pure function that assembles all metrics from
    pre-fetched series — the main test target.
  - compute_and_store_metrics(): async I/O wrapper that fetches prices + history,
    calls compute_all_metrics, and upserts into portfolio_metrics.
"""
from __future__ import annotations

import math
import uuid
from dataclasses import dataclass
from datetime import date, datetime, timezone

import numpy as np
import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.clients.market_data import MarketDataClient
from app.core.config import settings
from app.models.portfolio_metrics import PortfolioMetrics
from app.models.transaction import Transaction
from app.repositories.portfolio_metrics_repo import PortfolioMetricsRepository

logger = structlog.get_logger()

TRADING_DAYS = 252
NIFTY50_SYMBOL = "^NSEI"
# Rolling window for volatility/sharpe/drawdown/beta (trading days)
ROLLING_WINDOW = 30


# ---------------------------------------------------------------------------
# Data shapes
# ---------------------------------------------------------------------------


@dataclass
class HoldingSnapshot:
    symbol: str
    quantity: float
    avg_price: float


@dataclass
class PortfolioMetricsResult:
    total_value: float
    cost_basis: float
    unrealized_pnl: float
    realized_pnl: float
    daily_return: float | None
    volatility: float | None
    sharpe_ratio: float | None
    max_drawdown: float | None
    beta: float | None
    alpha: float | None


# ---------------------------------------------------------------------------
# Pure math helpers
# ---------------------------------------------------------------------------


def _daily_return(today_value: float, yesterday_value: float) -> float | None:
    if yesterday_value == 0:
        return None
    return (today_value - yesterday_value) / yesterday_value


def _volatility(daily_returns: np.ndarray) -> float | None:
    """Annualized std of daily returns. Requires >= 2 observations."""
    if len(daily_returns) < 2:
        return None
    return float(np.std(daily_returns, ddof=1) * math.sqrt(TRADING_DAYS))


def _sharpe_ratio(daily_returns: np.ndarray) -> float | None:
    """Sharpe ratio = mean / std * sqrt(252). Requires >= 2 observations."""
    if len(daily_returns) < 2:
        return None
    std = float(np.std(daily_returns, ddof=1))
    if std == 0:
        return None
    return float(np.mean(daily_returns) / std * math.sqrt(TRADING_DAYS))


def _max_drawdown(values: np.ndarray) -> float:
    """Max peak-to-trough decline. Returns a negative number (or 0)."""
    if len(values) < 2:
        return 0.0
    peak = np.maximum.accumulate(values)
    # Avoid divide-by-zero when peak contains zeros
    with np.errstate(invalid="ignore", divide="ignore"):
        drawdowns = np.where(peak > 0, (values - peak) / peak, 0.0)
    return float(np.min(drawdowns))


def _beta(
    portfolio_returns: np.ndarray, benchmark_returns: np.ndarray
) -> float | None:
    """Beta = cov(port, bench) / var(bench). Returns None if var(bench) == 0."""
    n = min(len(portfolio_returns), len(benchmark_returns))
    if n < 2:
        return None
    pr = portfolio_returns[-n:]
    br = benchmark_returns[-n:]
    bench_var = float(np.var(br, ddof=1))
    if bench_var == 0:
        return None
    cov = float(np.cov(pr, br, ddof=1)[0, 1])
    return cov / bench_var


def _alpha(
    portfolio_ann_return: float,
    beta: float,
    benchmark_ann_return: float,
    risk_free_rate: float,
) -> float:
    """Jensen's alpha: port_ann - (rfr + beta * (bench_ann - rfr))."""
    return portfolio_ann_return - (risk_free_rate + beta * (benchmark_ann_return - risk_free_rate))


# ---------------------------------------------------------------------------
# Public pure aggregator
# ---------------------------------------------------------------------------


def compute_all_metrics(
    today_value: float,
    cost_basis: float,
    realized_pnl: float,
    historical_values: list[float],
    benchmark_closes: list[float],
    risk_free_rate: float = settings.RISK_FREE_RATE,
) -> PortfolioMetricsResult:
    """Compute all portfolio metrics from pre-fetched series.

    Args:
        today_value: Current total portfolio value.
        cost_basis: Sum of (quantity * avg_price) for all current holdings.
        realized_pnl: Accumulated realized PnL from closed positions.
        historical_values: Past total_value snapshots, oldest first (up to 31).
            Needs >= 1 entry for daily_return; >= 2 for rolling metrics.
        benchmark_closes: Nifty 50 closes aligned to cover the same period as
            historical_values + today (len = len(historical_values) + 1 ideally).
        risk_free_rate: Annual risk-free rate (default from settings).
    """
    unrealized_pnl = today_value - cost_basis

    # Build full value series: history + today
    all_values = np.array(historical_values + [today_value], dtype=float)

    # Daily return from the most recent pair
    d_return: float | None = None
    if len(all_values) >= 2:
        d_return = _daily_return(float(all_values[-1]), float(all_values[-2]))

    # Return series from full value array
    port_returns = np.array([], dtype=float)
    if len(all_values) >= 2:
        with np.errstate(invalid="ignore", divide="ignore"):
            port_returns = np.where(
                all_values[:-1] > 0,
                np.diff(all_values) / all_values[:-1],
                0.0,
            )

    # Take last ROLLING_WINDOW returns for rolling metrics
    window_returns = port_returns[-ROLLING_WINDOW:]

    vol = _volatility(window_returns)
    sharpe = _sharpe_ratio(window_returns)
    drawdown = _max_drawdown(all_values[-ROLLING_WINDOW - 1 :]) if len(all_values) >= 2 else 0.0

    # Benchmark returns (aligned to same window)
    beta: float | None = None
    alpha: float | None = None
    if len(benchmark_closes) >= 2:
        bench_arr = np.array(benchmark_closes, dtype=float)
        with np.errstate(invalid="ignore", divide="ignore"):
            bench_returns = np.where(
                bench_arr[:-1] > 0,
                np.diff(bench_arr) / bench_arr[:-1],
                0.0,
            )
        # Align lengths: take last N matching portfolio window
        n_align = min(len(window_returns), len(bench_returns))
        if n_align >= 2:
            beta = _beta(window_returns[-n_align:], bench_returns[-n_align:])
            if beta is not None:
                port_ann = float(np.mean(window_returns[-n_align:])) * TRADING_DAYS
                bench_ann = float(np.mean(bench_returns[-n_align:])) * TRADING_DAYS
                alpha = _alpha(port_ann, beta, bench_ann, risk_free_rate)

    return PortfolioMetricsResult(
        total_value=today_value,
        cost_basis=cost_basis,
        unrealized_pnl=unrealized_pnl,
        realized_pnl=realized_pnl,
        daily_return=d_return,
        volatility=vol,
        sharpe_ratio=sharpe,
        max_drawdown=drawdown,
        beta=beta,
        alpha=alpha,
    )


# ---------------------------------------------------------------------------
# Realized PnL helper — derived from transaction history
# ---------------------------------------------------------------------------


async def get_realized_pnl(session: AsyncSession, portfolio_id: uuid.UUID) -> float:
    """Compute realized PnL without stored avg_price at sell time.

    Formula: total_sell_proceeds - total_buy_costs + current_cost_basis
    This is algebraically equivalent to sum(sell_pnl) under AVCO and avoids
    replaying the full transaction history with running avg.
    """
    result = await session.execute(
        select(Transaction).where(Transaction.portfolio_id == portfolio_id)
    )
    transactions = list(result.scalars().all())

    total_buy_cost = sum(
        float(tx.quantity) * float(tx.price)
        for tx in transactions
        if tx.transaction_type == "buy"
    )
    total_sell_proceeds = sum(
        float(tx.quantity) * float(tx.price)
        for tx in transactions
        if tx.transaction_type == "sell"
    )
    # Current cost basis from holdings (fetched separately by caller and passed in)
    # is added outside this function; here we return the raw buy/sell delta.
    # Full formula is: realized_pnl = total_sell_proceeds - total_buy_cost + cost_basis
    # We return the partial sum; the caller must add cost_basis.
    return total_sell_proceeds - total_buy_cost


# ---------------------------------------------------------------------------
# Async I/O wrapper
# ---------------------------------------------------------------------------


async def compute_and_store_metrics(
    session: AsyncSession,
    portfolio_id: uuid.UUID,
    holdings: list[HoldingSnapshot],
    market_client: MarketDataClient,
    for_date: date | None = None,
) -> PortfolioMetrics:
    """Fetch prices + history, compute metrics, upsert into portfolio_metrics.

    Args:
        session: Active async DB session.
        portfolio_id: Target portfolio.
        holdings: Current holdings (symbol, quantity, avg_price).
        market_client: Injected client; pass a mock in tests.
        for_date: Snapshot date (defaults to today UTC).
    """
    if for_date is None:
        for_date = datetime.now(timezone.utc).date()

    # --- Fetch current prices for held symbols ---
    prices: dict[str, float] = {}
    for h in holdings:
        closes = await market_client.get_daily_closes(h.symbol, limit=1)
        if closes:
            prices[h.symbol] = closes[-1]
        else:
            logger.warning("price_fetch_failed", symbol=h.symbol, portfolio_id=str(portfolio_id))

    # --- Compute today_value and cost_basis ---
    today_value = sum(h.quantity * prices.get(h.symbol, 0.0) for h in holdings)
    cost_basis = sum(h.quantity * h.avg_price for h in holdings)

    # --- Realized PnL ---
    partial_pnl = await get_realized_pnl(session, portfolio_id)
    realized_pnl = partial_pnl + cost_basis

    # --- Historical portfolio values (last 31 rows for 30-day window) ---
    metrics_repo = PortfolioMetricsRepository(session)
    past_rows = await metrics_repo.get_recent(portfolio_id, limit=ROLLING_WINDOW + 1)
    historical_values = [float(r.total_value) for r in past_rows]

    # --- Nifty 50 historical closes ---
    # Need len(historical_values) + 1 closes to produce len(historical_values) returns
    bench_limit = len(historical_values) + 2  # +1 for today, +1 buffer
    benchmark_closes = await market_client.get_daily_closes(
        NIFTY50_SYMBOL, limit=max(bench_limit, 2)
    )

    # --- Compute all metrics ---
    result = compute_all_metrics(
        today_value=today_value,
        cost_basis=cost_basis,
        realized_pnl=realized_pnl,
        historical_values=historical_values,
        benchmark_closes=benchmark_closes,
    )

    # --- Persist ---
    row = await metrics_repo.upsert(
        portfolio_id=portfolio_id,
        for_date=for_date,
        total_value=result.total_value,
        daily_return=result.daily_return,
        sharpe_ratio=result.sharpe_ratio,
        max_drawdown=result.max_drawdown,
        volatility=result.volatility,
        beta=result.beta,
        alpha=result.alpha,
        cost_basis=result.cost_basis,
        unrealized_pnl=result.unrealized_pnl,
        realized_pnl=realized_pnl,
    )
    await session.commit()

    logger.info(
        "metrics_stored",
        portfolio_id=str(portfolio_id),
        date=str(for_date),
        total_value=result.total_value,
        sharpe=result.sharpe_ratio,
    )
    return row
