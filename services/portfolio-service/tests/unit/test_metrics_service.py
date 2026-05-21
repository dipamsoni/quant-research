"""Unit tests for app/services/metrics.py.

All tests use synthetic return series — no real API calls, no DB.
"""
from __future__ import annotations

import math

import numpy as np
import pytest

from app.services.metrics import (
    TRADING_DAYS,
    HoldingSnapshot,
    PortfolioMetricsResult,
    _alpha,
    _beta,
    _daily_return,
    _max_drawdown,
    _sharpe_ratio,
    _volatility,
    compute_all_metrics,
)

# ---------------------------------------------------------------------------
# _daily_return
# ---------------------------------------------------------------------------


class TestDailyReturn:
    def test_positive_return(self) -> None:
        assert _daily_return(110.0, 100.0) == pytest.approx(0.10)

    def test_negative_return(self) -> None:
        assert _daily_return(90.0, 100.0) == pytest.approx(-0.10)

    def test_flat(self) -> None:
        assert _daily_return(100.0, 100.0) == pytest.approx(0.0)

    def test_zero_yesterday_returns_none(self) -> None:
        assert _daily_return(100.0, 0.0) is None


# ---------------------------------------------------------------------------
# _volatility
# ---------------------------------------------------------------------------


class TestVolatility:
    def test_known_std(self) -> None:
        # daily returns of 1% and 3%: std = 1%, annualized = 1% * sqrt(252)
        returns = np.array([0.01, 0.03, 0.01, 0.03] * 5)
        vol = _volatility(returns)
        assert vol is not None
        assert vol == pytest.approx(np.std(returns, ddof=1) * math.sqrt(TRADING_DAYS))

    def test_single_observation_returns_none(self) -> None:
        assert _volatility(np.array([0.01])) is None

    def test_empty_returns_none(self) -> None:
        assert _volatility(np.array([])) is None

    def test_zero_variance_series(self) -> None:
        returns = np.array([0.01] * 30)
        vol = _volatility(returns)
        assert vol == pytest.approx(0.0)


# ---------------------------------------------------------------------------
# _sharpe_ratio
# ---------------------------------------------------------------------------


class TestSharpeRatio:
    def test_known_sharpe(self) -> None:
        returns = np.array([0.001] * 15 + [0.003] * 15)
        expected = np.mean(returns) / np.std(returns, ddof=1) * math.sqrt(TRADING_DAYS)
        assert _sharpe_ratio(returns) == pytest.approx(expected)

    def test_zero_std_returns_none(self) -> None:
        assert _sharpe_ratio(np.array([0.01, 0.01, 0.01])) is None

    def test_single_observation_returns_none(self) -> None:
        assert _sharpe_ratio(np.array([0.01])) is None

    def test_positive_sharpe_for_positive_returns(self) -> None:
        returns = np.array([0.002, 0.003, 0.001, 0.004, 0.002] * 6)
        assert _sharpe_ratio(returns) > 0  # type: ignore[operator]

    def test_negative_sharpe_for_negative_returns(self) -> None:
        returns = np.array([-0.002, -0.003, -0.001, -0.004, -0.002] * 6)
        assert _sharpe_ratio(returns) < 0  # type: ignore[operator]


# ---------------------------------------------------------------------------
# _max_drawdown
# ---------------------------------------------------------------------------


class TestMaxDrawdown:
    def test_known_drawdown(self) -> None:
        # peak 100, trough 50 → -50%
        values = np.array([100.0, 90.0, 80.0, 70.0, 60.0, 50.0, 60.0, 70.0])
        assert _max_drawdown(values) == pytest.approx(-0.50)

    def test_monotone_increase_zero_drawdown(self) -> None:
        values = np.array([100.0, 110.0, 120.0, 130.0])
        assert _max_drawdown(values) == pytest.approx(0.0)

    def test_flat_series_zero_drawdown(self) -> None:
        values = np.array([100.0, 100.0, 100.0])
        assert _max_drawdown(values) == pytest.approx(0.0)

    def test_single_value_zero_drawdown(self) -> None:
        assert _max_drawdown(np.array([100.0])) == pytest.approx(0.0)

    def test_multiple_troughs_picks_deepest(self) -> None:
        # First dip: 100→80 = -20%; second dip: 120→60 = -50%
        values = np.array([100.0, 80.0, 120.0, 60.0])
        assert _max_drawdown(values) == pytest.approx(-0.50)


# ---------------------------------------------------------------------------
# _beta
# ---------------------------------------------------------------------------


class TestBeta:
    def test_unit_beta_when_identical(self) -> None:
        r = np.array([0.01, -0.02, 0.015, -0.005, 0.02] * 4)
        assert _beta(r, r) == pytest.approx(1.0)

    def test_zero_variance_benchmark_returns_none(self) -> None:
        port = np.array([0.01, 0.02, 0.03])
        bench = np.array([0.01, 0.01, 0.01])  # var = 0
        assert _beta(port, bench) is None

    def test_single_observation_returns_none(self) -> None:
        assert _beta(np.array([0.01]), np.array([0.01])) is None

    def test_beta_calculation(self) -> None:
        # port = 2 * bench → beta ≈ 2
        bench = np.array([0.01, -0.02, 0.015, -0.01, 0.005] * 4)
        port = 2.0 * bench
        assert _beta(port, bench) == pytest.approx(2.0, rel=1e-6)

    def test_negative_beta(self) -> None:
        bench = np.array([0.01, -0.02, 0.015, -0.01, 0.005] * 4)
        port = -1.0 * bench
        assert _beta(port, bench) == pytest.approx(-1.0, rel=1e-6)


# ---------------------------------------------------------------------------
# _alpha
# ---------------------------------------------------------------------------


class TestAlpha:
    def test_zero_alpha_when_perfectly_explained_by_capm(self) -> None:
        rfr = 0.065
        beta = 1.5
        bench_ann = 0.12
        port_ann = rfr + beta * (bench_ann - rfr)
        assert _alpha(port_ann, beta, bench_ann, rfr) == pytest.approx(0.0)

    def test_positive_alpha(self) -> None:
        rfr = 0.065
        beta = 1.0
        bench_ann = 0.10
        port_ann = 0.15  # outperforms by 5%
        alpha = _alpha(port_ann, beta, bench_ann, rfr)
        assert alpha == pytest.approx(0.05)

    def test_negative_alpha(self) -> None:
        rfr = 0.065
        beta = 1.0
        bench_ann = 0.10
        port_ann = 0.06  # underperforms
        alpha = _alpha(port_ann, beta, bench_ann, rfr)
        assert alpha == pytest.approx(-0.04)


# ---------------------------------------------------------------------------
# compute_all_metrics — integration of the pure layer
# ---------------------------------------------------------------------------


def _make_value_series(n: int = 32, daily_drift: float = 0.001) -> list[float]:
    """Synthetic portfolio value series with small daily drift + noise."""
    rng = np.random.default_rng(42)
    start = 1_000_000.0
    values = [start]
    for _ in range(n - 1):
        ret = daily_drift + rng.normal(0, 0.01)
        values.append(values[-1] * (1 + ret))
    return values


def _make_bench_series(n: int = 33) -> list[float]:
    rng = np.random.default_rng(7)
    start = 20_000.0  # Nifty 50 base
    values = [start]
    for _ in range(n - 1):
        ret = 0.0005 + rng.normal(0, 0.008)
        values.append(values[-1] * (1 + ret))
    return values


class TestComputeAllMetrics:
    def _run(
        self,
        n_history: int = 31,
        bench_n: int = 33,
    ) -> PortfolioMetricsResult:
        series = _make_value_series(n_history + 1)
        today = series[-1]
        history = series[:-1]
        bench = _make_bench_series(bench_n)
        holdings = [HoldingSnapshot(symbol="RELIANCE", quantity=100, avg_price=2000.0)]
        cost_basis = 100 * 2000.0
        realized_pnl = 50_000.0
        return compute_all_metrics(
            today_value=today,
            cost_basis=cost_basis,
            realized_pnl=realized_pnl,
            historical_values=history,
            benchmark_closes=bench,
        )

    def test_basic_fields_present(self) -> None:
        result = self._run()
        assert result.total_value > 0
        assert result.cost_basis == pytest.approx(200_000.0)
        assert result.realized_pnl == pytest.approx(50_000.0)

    def test_unrealized_pnl_formula(self) -> None:
        result = self._run()
        assert result.unrealized_pnl == pytest.approx(result.total_value - result.cost_basis)

    def test_daily_return_computable_with_history(self) -> None:
        result = self._run(n_history=5)
        assert result.daily_return is not None

    def test_rolling_metrics_computable_with_30_history(self) -> None:
        result = self._run(n_history=31)
        assert result.volatility is not None
        assert result.sharpe_ratio is not None
        assert result.max_drawdown is not None

    def test_beta_alpha_computable_with_benchmark(self) -> None:
        result = self._run(n_history=31, bench_n=35)
        assert result.beta is not None
        assert result.alpha is not None

    def test_max_drawdown_non_positive(self) -> None:
        result = self._run()
        assert result.max_drawdown <= 0.0  # type: ignore[operator]

    def test_volatility_non_negative(self) -> None:
        result = self._run()
        assert result.volatility >= 0.0  # type: ignore[operator]

    def test_no_history_returns_none_for_rolling_metrics(self) -> None:
        series = _make_value_series(1)
        result = compute_all_metrics(
            today_value=series[0],
            cost_basis=200_000.0,
            realized_pnl=0.0,
            historical_values=[],
            benchmark_closes=[20_000.0],
        )
        assert result.daily_return is None
        assert result.volatility is None
        assert result.sharpe_ratio is None
        assert result.beta is None
        assert result.alpha is None

    def test_one_history_has_daily_return_but_no_rolling(self) -> None:
        result = compute_all_metrics(
            today_value=1_010_000.0,
            cost_basis=1_000_000.0,
            realized_pnl=0.0,
            historical_values=[1_000_000.0],
            benchmark_closes=[20_000.0, 20_100.0],
        )
        assert result.daily_return == pytest.approx(0.01)
        assert result.volatility is None
        assert result.sharpe_ratio is None
        assert result.beta is None

    def test_daily_return_correct_sign(self) -> None:
        # Value fell from 1_000_000 to 950_000 → -5%
        result = compute_all_metrics(
            today_value=950_000.0,
            cost_basis=900_000.0,
            realized_pnl=0.0,
            historical_values=[1_000_000.0],
            benchmark_closes=[20_000.0, 19_000.0],
        )
        assert result.daily_return == pytest.approx(-0.05)
