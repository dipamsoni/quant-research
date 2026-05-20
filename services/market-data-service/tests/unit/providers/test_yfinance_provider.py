from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import patch

import pandas as pd
import pytest

from app.providers.yfinance_provider import YFinanceProvider


def _make_df() -> pd.DataFrame:
    index = pd.DatetimeIndex(
        [
            datetime(2024, 1, 2, tzinfo=timezone.utc),
            datetime(2024, 1, 3, tzinfo=timezone.utc),
        ],
        name="Date",
    )
    return pd.DataFrame(
        {
            "Open": [185.0, 186.5],
            "High": [187.0, 188.0],
            "Low": [183.0, 185.5],
            "Close": [186.0, 187.0],
            "Volume": [80_000_000.0, 75_000_000.0],
        },
        index=index,
    )


@pytest.fixture
def provider() -> YFinanceProvider:
    return YFinanceProvider()


@pytest.fixture
def date_range() -> tuple[datetime, datetime]:
    return datetime(2024, 1, 1, tzinfo=timezone.utc), datetime(2024, 1, 10, tzinfo=timezone.utc)


class TestYFinanceProvider:
    def test_source_name(self, provider: YFinanceProvider) -> None:
        assert provider.source_name == "yfinance"

    def test_supports_valid_timeframes(self, provider: YFinanceProvider) -> None:
        for tf in ["1m", "5m", "15m", "30m", "1h", "1d", "1w"]:
            assert provider.supports_timeframe(tf), f"expected {tf!r} to be supported"

    def test_does_not_support_4h(self, provider: YFinanceProvider) -> None:
        assert not provider.supports_timeframe("4h")

    async def test_get_historical_returns_candles(
        self, provider: YFinanceProvider, date_range: tuple[datetime, datetime]
    ) -> None:
        start, end = date_range
        with patch("app.providers.yfinance_provider.yf.download", return_value=_make_df()):
            candles = await provider.get_historical("AAPL", "1d", start, end)

        assert len(candles) == 2
        c = candles[0]
        assert c.symbol == "AAPL"
        assert c.timeframe == "1d"
        assert c.open == Decimal("185.0")
        assert c.high == Decimal("187.0")
        assert c.low == Decimal("183.0")
        assert c.close == Decimal("186.0")
        assert c.volume == Decimal("80000000.0")
        assert c.source == "yfinance"
        assert c.vwap is None
        assert c.trade_count is None
        assert c.time.tzinfo is not None

    async def test_get_historical_empty_df_returns_empty(
        self, provider: YFinanceProvider, date_range: tuple[datetime, datetime]
    ) -> None:
        start, end = date_range
        empty_df = pd.DataFrame(columns=["Open", "High", "Low", "Close", "Volume"])
        with patch("app.providers.yfinance_provider.yf.download", return_value=empty_df):
            candles = await provider.get_historical("AAPL", "1d", start, end)
        assert candles == []

    async def test_unsupported_timeframe_raises(
        self, provider: YFinanceProvider, date_range: tuple[datetime, datetime]
    ) -> None:
        start, end = date_range
        with pytest.raises(ValueError, match="yfinance does not support timeframe '4h'"):
            await provider.get_historical("AAPL", "4h", start, end)

    async def test_tz_naive_index_gets_utc(
        self, provider: YFinanceProvider, date_range: tuple[datetime, datetime]
    ) -> None:
        start, end = date_range
        # yfinance sometimes returns tz-naive index for daily data
        tz_naive_df = _make_df().copy()
        tz_naive_df.index = tz_naive_df.index.tz_localize(None)
        with patch("app.providers.yfinance_provider.yf.download", return_value=tz_naive_df):
            candles = await provider.get_historical("AAPL", "1d", start, end)
        assert all(c.time.tzinfo == timezone.utc for c in candles)

    def test_multiindex_columns_flattened(self, provider: YFinanceProvider) -> None:
        df = _make_df()
        # Simulate MultiIndex columns as returned by some yfinance versions
        df.columns = pd.MultiIndex.from_tuples(
            [(col, "AAPL") for col in df.columns], names=["Price", "Ticker"]
        )
        candles = provider._normalize(df, "AAPL", "1d")
        assert len(candles) == 2
        assert candles[0].open == Decimal("185.0")
