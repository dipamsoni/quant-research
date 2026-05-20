from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import patch

import pytest

from app.providers.binance_provider import BinanceProvider


def _make_klines() -> list[list]:
    return [
        [
            1704153600000,   # open_time (2024-01-02 00:00:00 UTC)
            "43000.00",      # open
            "44000.00",      # high
            "42500.00",      # low
            "43500.00",      # close
            "100.0",         # volume (base)
            1704239999000,   # close_time
            "4325000.0",     # quote_asset_volume
            150,             # number_of_trades
            "60.0",          # taker_buy_base_volume
            "2595000.0",     # taker_buy_quote_volume
            "0",             # ignore
        ]
    ]


@pytest.fixture
def provider() -> BinanceProvider:
    with patch("app.providers.binance_provider.Client"):
        return BinanceProvider()


@pytest.fixture
def date_range() -> tuple[datetime, datetime]:
    return datetime(2024, 1, 1, tzinfo=timezone.utc), datetime(2024, 1, 10, tzinfo=timezone.utc)


class TestBinanceProvider:
    def test_source_name(self, provider: BinanceProvider) -> None:
        assert provider.source_name == "binance"

    def test_supports_4h(self, provider: BinanceProvider) -> None:
        assert provider.supports_timeframe("4h")

    def test_supports_all_canonical_timeframes(self, provider: BinanceProvider) -> None:
        for tf in ["1m", "5m", "15m", "30m", "1h", "4h", "1d", "1w"]:
            assert provider.supports_timeframe(tf), f"expected {tf!r} to be supported"

    def test_does_not_support_unknown_timeframe(self, provider: BinanceProvider) -> None:
        assert not provider.supports_timeframe("3d")

    async def test_get_historical_returns_candles(
        self, provider: BinanceProvider, date_range: tuple[datetime, datetime]
    ) -> None:
        start, end = date_range
        provider._client.get_klines.return_value = _make_klines()
        candles = await provider.get_historical("BTCUSDT", "1d", start, end)

        assert len(candles) == 1
        c = candles[0]
        assert c.symbol == "BTCUSDT"
        assert c.timeframe == "1d"
        assert c.open == Decimal("43000.00")
        assert c.high == Decimal("44000.00")
        assert c.low == Decimal("42500.00")
        assert c.close == Decimal("43500.00")
        assert c.volume == Decimal("100.0")
        assert c.trade_count == 150
        assert c.source == "binance"
        assert c.time == datetime(2024, 1, 2, 0, 0, 0, tzinfo=timezone.utc)

    def test_vwap_computed_from_quote_volume(self, provider: BinanceProvider) -> None:
        candles = provider._normalize(_make_klines(), "BTCUSDT", "1d")
        expected_vwap = Decimal("4325000.0") / Decimal("100.0")
        assert candles[0].vwap == expected_vwap

    def test_vwap_none_when_zero_volume(self, provider: BinanceProvider) -> None:
        kline = _make_klines()[0].copy()
        kline[5] = "0.0"   # zero base volume
        kline[7] = "0.0"
        candles = provider._normalize([kline], "BTCUSDT", "1d")
        assert candles[0].vwap is None

    async def test_empty_klines_returns_empty(
        self, provider: BinanceProvider, date_range: tuple[datetime, datetime]
    ) -> None:
        start, end = date_range
        provider._client.get_klines.return_value = []
        candles = await provider.get_historical("BTCUSDT", "1d", start, end)
        assert candles == []

    async def test_unsupported_timeframe_raises(
        self, provider: BinanceProvider, date_range: tuple[datetime, datetime]
    ) -> None:
        start, end = date_range
        with pytest.raises(ValueError, match="Binance does not support timeframe '3d'"):
            await provider.get_historical("BTCUSDT", "3d", start, end)

    def test_time_is_utc(self, provider: BinanceProvider) -> None:
        candles = provider._normalize(_make_klines(), "BTCUSDT", "1d")
        assert candles[0].time.tzinfo == timezone.utc
