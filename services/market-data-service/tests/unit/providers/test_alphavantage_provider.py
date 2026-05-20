from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pandas as pd
import pytest

import app.providers.alphavantage_provider as av_mod
from app.providers.alphavantage_provider import AlphaVantageProvider


def _make_av_df() -> pd.DataFrame:
    # alpha_vantage returns tz-naive DatetimeIndex
    index = pd.DatetimeIndex(
        [datetime(2024, 1, 2), datetime(2024, 1, 3)],
        name="date",
    )
    return pd.DataFrame(
        {
            "1. open": [185.0, 186.5],
            "2. high": [187.0, 188.0],
            "3. low": [183.0, 185.5],
            "4. close": [186.0, 187.0],
            "5. volume": [80_000_000.0, 75_000_000.0],
        },
        index=index,
    )


@pytest.fixture
def provider() -> AlphaVantageProvider:
    return AlphaVantageProvider(api_key="test_key")


@pytest.fixture
def date_range() -> tuple[datetime, datetime]:
    return datetime(2024, 1, 1, tzinfo=timezone.utc), datetime(2024, 1, 10, tzinfo=timezone.utc)


class TestAVRateLimit:
    """Unit tests for the module-level rate limiter (real function, no mock)."""

    async def test_first_call_after_long_idle_does_not_sleep(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        import asyncio

        monkeypatch.setattr(av_mod, "_av_last_call_at", 0.0)
        sleep_calls: list[float] = []

        async def _fake_sleep(s: float) -> None:
            sleep_calls.append(s)

        monkeypatch.setattr(asyncio, "sleep", _fake_sleep)
        await av_mod._av_rate_limit()
        # Process uptime >> 12 s → wait is negative → no sleep.
        assert sleep_calls == []

    async def test_rapid_second_call_sleeps(self, monkeypatch: pytest.MonkeyPatch) -> None:
        import asyncio
        import time

        # Simulate _av_last_call_at set to "just now" (11 s ago → need 1 more s).
        monkeypatch.setattr(av_mod, "_av_last_call_at", time.monotonic() - 11.0)

        sleep_calls: list[float] = []

        async def _fake_sleep(s: float) -> None:
            sleep_calls.append(s)

        monkeypatch.setattr(asyncio, "sleep", _fake_sleep)
        await av_mod._av_rate_limit()

        assert len(sleep_calls) == 1
        assert 0 < sleep_calls[0] <= av_mod._AV_MIN_INTERVAL

    async def test_sleep_duration_decreases_as_time_passes(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        import asyncio
        import time

        elapsed = 9.0  # 9 s since last call → need 3 more s
        monkeypatch.setattr(av_mod, "_av_last_call_at", time.monotonic() - elapsed)

        sleep_calls: list[float] = []

        async def _fake_sleep(s: float) -> None:
            sleep_calls.append(s)

        monkeypatch.setattr(asyncio, "sleep", _fake_sleep)
        await av_mod._av_rate_limit()

        assert len(sleep_calls) == 1
        assert 2.0 < sleep_calls[0] < av_mod._AV_MIN_INTERVAL - elapsed + 1.0


class TestAlphaVantageProvider:
    @pytest.fixture(autouse=True)
    def _no_rate_limit(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Bypass the 12 s inter-call sleep so these unit tests finish instantly."""
        monkeypatch.setattr(av_mod, "_av_rate_limit", AsyncMock())
    def test_source_name(self, provider: AlphaVantageProvider) -> None:
        assert provider.source_name == "alphavantage"

    def test_requires_api_key(self) -> None:
        with pytest.raises(ValueError, match="requires an API key"):
            AlphaVantageProvider(api_key="")

    def test_supports_intraday_timeframes(self, provider: AlphaVantageProvider) -> None:
        for tf in ["1m", "5m", "15m", "30m", "1h"]:
            assert provider.supports_timeframe(tf), f"expected {tf!r} to be supported"

    def test_supports_daily_and_weekly(self, provider: AlphaVantageProvider) -> None:
        assert provider.supports_timeframe("1d")
        assert provider.supports_timeframe("1w")

    def test_does_not_support_4h(self, provider: AlphaVantageProvider) -> None:
        assert not provider.supports_timeframe("4h")

    async def test_get_historical_intraday(
        self, provider: AlphaVantageProvider, date_range: tuple[datetime, datetime]
    ) -> None:
        start, end = date_range
        mock_ts = MagicMock()
        mock_ts.get_intraday.return_value = (_make_av_df(), {})
        with patch("app.providers.alphavantage_provider.TimeSeries", return_value=mock_ts):
            candles = await provider.get_historical("IBM", "5m", start, end)

        assert len(candles) == 2
        c = candles[0]
        assert c.symbol == "IBM"
        assert c.timeframe == "5m"
        assert c.open == Decimal("185.0")
        assert c.high == Decimal("187.0")
        assert c.low == Decimal("183.0")
        assert c.close == Decimal("186.0")
        assert c.volume == Decimal("80000000.0")
        assert c.source == "alphavantage"
        assert c.time.tzinfo is not None
        # Verify intraday endpoint was called with correct interval
        mock_ts.get_intraday.assert_called_once_with(
            symbol="IBM", interval="5min", outputsize="full"
        )

    async def test_get_historical_daily(
        self, provider: AlphaVantageProvider, date_range: tuple[datetime, datetime]
    ) -> None:
        start, end = date_range
        mock_ts = MagicMock()
        mock_ts.get_daily.return_value = (_make_av_df(), {})
        with patch("app.providers.alphavantage_provider.TimeSeries", return_value=mock_ts):
            candles = await provider.get_historical("IBM", "1d", start, end)

        assert len(candles) == 2
        assert candles[0].timeframe == "1d"
        mock_ts.get_daily.assert_called_once_with(symbol="IBM", outputsize="full")

    async def test_get_historical_weekly(
        self, provider: AlphaVantageProvider, date_range: tuple[datetime, datetime]
    ) -> None:
        start, end = date_range
        mock_ts = MagicMock()
        mock_ts.get_weekly.return_value = (_make_av_df(), {})
        with patch("app.providers.alphavantage_provider.TimeSeries", return_value=mock_ts):
            candles = await provider.get_historical("IBM", "1w", start, end)

        assert len(candles) == 2
        assert candles[0].timeframe == "1w"

    async def test_date_filter_excludes_out_of_range(
        self, provider: AlphaVantageProvider
    ) -> None:
        # AV returns full history; provider must filter to [start, end]
        start = datetime(2024, 1, 3, tzinfo=timezone.utc)
        end = datetime(2024, 1, 3, tzinfo=timezone.utc)
        mock_ts = MagicMock()
        mock_ts.get_daily.return_value = (_make_av_df(), {})
        with patch("app.providers.alphavantage_provider.TimeSeries", return_value=mock_ts):
            candles = await provider.get_historical("IBM", "1d", start, end)
        # Only Jan 3 row should survive
        assert len(candles) == 1
        assert candles[0].time.day == 3

    async def test_unsupported_timeframe_raises(
        self, provider: AlphaVantageProvider, date_range: tuple[datetime, datetime]
    ) -> None:
        start, end = date_range
        with pytest.raises(ValueError, match="AlphaVantage does not support timeframe '4h'"):
            await provider.get_historical("IBM", "4h", start, end)

    async def test_empty_df_returns_empty(
        self, provider: AlphaVantageProvider, date_range: tuple[datetime, datetime]
    ) -> None:
        start, end = date_range
        empty_df = pd.DataFrame(
            columns=["1. open", "2. high", "3. low", "4. close", "5. volume"]
        )
        mock_ts = MagicMock()
        mock_ts.get_daily.return_value = (empty_df, {})
        with patch("app.providers.alphavantage_provider.TimeSeries", return_value=mock_ts):
            candles = await provider.get_historical("IBM", "1d", start, end)
        assert candles == []
