"""Tests for gap detection and backfill pipeline."""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.pipelines.ohlcv_pipeline import (
    _detect_gaps,
    _gap_threshold,
    backfill,
)
from app.providers.base import OHLCVCandleSchema

_EQUITY = "equity"
_CRYPTO = "crypto"


def _candle(dt: datetime, symbol: str = "AAPL", timeframe: str = "1d") -> OHLCVCandleSchema:
    return OHLCVCandleSchema(
        time=dt,
        symbol=symbol,
        timeframe=timeframe,
        open=Decimal("100"),
        high=Decimal("105"),
        low=Decimal("98"),
        close=Decimal("102"),
        volume=Decimal("500000"),
        source="test",
    )


def _make_asset(
    symbol: str = "AAPL",
    asset_type: str = "equity",
) -> MagicMock:
    asset = MagicMock()
    asset.id = uuid.uuid4()
    asset.symbol = symbol
    asset.asset_type = asset_type
    return asset


# ---------------------------------------------------------------------------
# _gap_threshold
# ---------------------------------------------------------------------------

class TestGapThreshold:
    def test_unknown_timeframe_returns_zero(self) -> None:
        assert _gap_threshold("3d", _EQUITY) == 0

    def test_daily_equity_is_3x_expected(self) -> None:
        assert _gap_threshold("1d", _EQUITY) == 86400 * 3

    def test_daily_crypto_is_3x_expected(self) -> None:
        assert _gap_threshold("1d", _CRYPTO) == 86400 * 3

    def test_weekly_equity_is_3x_expected(self) -> None:
        assert _gap_threshold("1w", _EQUITY) == 604800 * 3

    def test_intraday_equity_uses_36h_threshold(self) -> None:
        for tf in ("1m", "5m", "15m", "30m", "1h", "4h"):
            assert _gap_threshold(tf, _EQUITY) == 36 * 3600, f"failed for {tf}"

    def test_intraday_crypto_uses_3x_expected(self) -> None:
        expected_seconds = {"1m": 60, "5m": 300, "15m": 900, "30m": 1800, "1h": 3600, "4h": 14400}
        for tf, exp in expected_seconds.items():
            assert _gap_threshold(tf, _CRYPTO) == exp * 3, f"failed for {tf}"


# ---------------------------------------------------------------------------
# _detect_gaps
# ---------------------------------------------------------------------------

class TestDetectGaps:
    def test_fewer_than_two_candles_returns_zero(self) -> None:
        t = datetime(2024, 1, 2, tzinfo=timezone.utc)
        assert _detect_gaps([], "1d", "AAPL") == 0
        assert _detect_gaps([_candle(t)], "1d", "AAPL") == 0

    def test_no_gaps_in_consecutive_daily_candles(self) -> None:
        base = datetime(2024, 1, 2, tzinfo=timezone.utc)
        candles = [_candle(base + timedelta(days=i)) for i in range(5)]
        assert _detect_gaps(candles, "1d", "AAPL", _EQUITY) == 0

    def test_detects_daily_gap_exceeding_3x_interval(self) -> None:
        base = datetime(2024, 1, 2, tzinfo=timezone.utc)
        # 4-day gap between candles (threshold = 3 days)
        candles = [_candle(base), _candle(base + timedelta(days=4))]
        assert _detect_gaps(candles, "1d", "AAPL", _EQUITY) == 1

    def test_no_false_positive_for_weekend_daily_gap(self) -> None:
        # Friday → Monday = 3-day gap, exactly at threshold → NOT flagged (delta == threshold)
        base = datetime(2024, 1, 5, tzinfo=timezone.utc)  # Friday
        candles = [_candle(base), _candle(base + timedelta(days=3))]
        gap_count = _detect_gaps(candles, "1d", "AAPL", _EQUITY)
        assert gap_count == 0

    def test_counts_multiple_gaps(self) -> None:
        base = datetime(2024, 1, 2, tzinfo=timezone.utc)
        candles = [
            _candle(base),
            _candle(base + timedelta(days=5)),   # gap 1
            _candle(base + timedelta(days=6)),
            _candle(base + timedelta(days=12)),  # gap 2
        ]
        assert _detect_gaps(candles, "1d", "AAPL", _EQUITY) == 2

    def test_handles_unsorted_input(self) -> None:
        base = datetime(2024, 1, 2, tzinfo=timezone.utc)
        # Deliberately reversed order — should still detect the gap after sorting.
        candles = [
            _candle(base + timedelta(days=5)),
            _candle(base),
        ]
        # 5-day gap → 1 gap detected (threshold for daily equity = 3 days)
        assert _detect_gaps(candles, "1d", "AAPL", _EQUITY) == 1

    def test_unknown_timeframe_threshold_zero_skips_check(self) -> None:
        base = datetime(2024, 1, 2, tzinfo=timezone.utc)
        # Timeframe not in _EXPECTED_SECONDS → threshold = 0 → no gap emitted
        candles = [_candle(base), _candle(base + timedelta(days=100))]
        assert _detect_gaps(candles, "3d", "AAPL", _EQUITY) == 0

    def test_intraday_equity_tolerates_overnight(self) -> None:
        # 1h candle 16:00 → next day 09:30 = 17.5 h — under the 36 h threshold
        base = datetime(2024, 1, 2, 16, 0, tzinfo=timezone.utc)
        next_open = datetime(2024, 1, 3, 9, 30, tzinfo=timezone.utc)
        candles = [
            _candle(base, timeframe="1h"),
            _candle(next_open, timeframe="1h"),
        ]
        assert _detect_gaps(candles, "1h", "AAPL", _EQUITY) == 0

    def test_intraday_crypto_flags_3h_gap_on_1h_timeframe(self) -> None:
        # 3× expected = 3 h; any gap > 3 h is anomalous for 24/7 crypto
        base = datetime(2024, 1, 2, tzinfo=timezone.utc)
        candles = [
            _candle(base, timeframe="1h"),
            _candle(base + timedelta(hours=4), timeframe="1h"),
        ]
        assert _detect_gaps(candles, "1h", "BTCUSDT", _CRYPTO) == 1


# ---------------------------------------------------------------------------
# backfill()
# ---------------------------------------------------------------------------

class TestBackfill:
    async def test_success_returns_inserted_count(self) -> None:
        base = datetime(2024, 1, 2, tzinfo=timezone.utc)
        candles = [_candle(base + timedelta(days=i)) for i in range(3)]
        asset = _make_asset()

        provider = MagicMock()
        provider.source_name = "test"
        provider.get_historical = AsyncMock(return_value=candles)

        db = AsyncMock()

        with (
            patch("app.pipelines.ohlcv_pipeline._get_boundary_candle", new=AsyncMock(return_value=None)),
            patch("app.pipelines.ohlcv_pipeline._upsert_candles", new=AsyncMock(return_value=3)) as mock_upsert,
        ):
            result = await backfill(db, asset, "1d", base, base + timedelta(days=3), provider)

        assert result == 3
        mock_upsert.assert_called_once_with(db, asset.id, candles)

    async def test_provider_exception_returns_zero(self) -> None:
        asset = _make_asset()
        provider = MagicMock()
        provider.source_name = "test"
        provider.get_historical = AsyncMock(side_effect=RuntimeError("provider down"))

        db = AsyncMock()
        base = datetime(2024, 1, 2, tzinfo=timezone.utc)

        with patch("app.pipelines.ohlcv_pipeline._upsert_candles") as mock_upsert:
            result = await backfill(db, asset, "1d", base, base + timedelta(days=1), provider)

        assert result == 0
        mock_upsert.assert_not_called()

    async def test_empty_candles_returns_zero(self) -> None:
        asset = _make_asset()
        provider = MagicMock()
        provider.source_name = "test"
        provider.get_historical = AsyncMock(return_value=[])

        db = AsyncMock()
        base = datetime(2024, 1, 2, tzinfo=timezone.utc)

        with patch("app.pipelines.ohlcv_pipeline._upsert_candles") as mock_upsert:
            result = await backfill(db, asset, "1d", base, base + timedelta(days=1), provider)

        assert result == 0
        mock_upsert.assert_not_called()

    async def test_boundary_candle_included_in_gap_check(self) -> None:
        """Boundary candle from prior run is prepended so cross-run gaps are caught."""
        base = datetime(2024, 1, 10, tzinfo=timezone.utc)
        # Boundary: Jan 5. New candle: Jan 10. Gap = 5 days > 3 day threshold → logged.
        boundary = _candle(datetime(2024, 1, 5, tzinfo=timezone.utc))
        new_candle = _candle(base)
        asset = _make_asset()

        provider = MagicMock()
        provider.source_name = "test"
        provider.get_historical = AsyncMock(return_value=[new_candle])

        db = AsyncMock()

        with (
            patch("app.pipelines.ohlcv_pipeline._get_boundary_candle", new=AsyncMock(return_value=boundary)),
            patch("app.pipelines.ohlcv_pipeline._upsert_candles", new=AsyncMock(return_value=1)),
            patch("app.pipelines.ohlcv_pipeline._detect_gaps") as mock_detect,
        ):
            await backfill(db, asset, "1d", base, base + timedelta(days=1), provider)

        # Verify boundary was prepended into the gap check call.
        called_candles = mock_detect.call_args[0][0]
        assert called_candles[0] == boundary
        assert called_candles[1] == new_candle

    async def test_crypto_asset_type_passed_to_gap_check(self) -> None:
        base = datetime(2024, 1, 2, tzinfo=timezone.utc)
        candles = [_candle(base)]
        asset = _make_asset(symbol="BTCUSDT", asset_type="crypto")

        provider = MagicMock()
        provider.source_name = "binance"
        provider.get_historical = AsyncMock(return_value=candles)

        db = AsyncMock()

        with (
            patch("app.pipelines.ohlcv_pipeline._get_boundary_candle", new=AsyncMock(return_value=None)),
            patch("app.pipelines.ohlcv_pipeline._upsert_candles", new=AsyncMock(return_value=1)),
            patch("app.pipelines.ohlcv_pipeline._detect_gaps") as mock_detect,
        ):
            await backfill(db, asset, "1d", base, base + timedelta(days=1), provider)

        _, _, _, asset_type_arg = mock_detect.call_args[0]
        assert asset_type_arg == "crypto"
