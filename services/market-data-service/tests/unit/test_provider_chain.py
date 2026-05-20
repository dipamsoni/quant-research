"""Tests for ProviderChain failover logic."""
from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.providers.base import MarketDataProvider, OHLCVCandleSchema, ProviderChain

_DATE_RANGE = (
    datetime(2024, 1, 1, tzinfo=timezone.utc),
    datetime(2024, 1, 10, tzinfo=timezone.utc),
)


def _candle(symbol: str = "AAPL") -> OHLCVCandleSchema:
    return OHLCVCandleSchema(
        time=datetime(2024, 1, 2, tzinfo=timezone.utc),
        symbol=symbol,
        timeframe="1d",
        open=Decimal("185"),
        high=Decimal("187"),
        low=Decimal("183"),
        close=Decimal("186"),
        volume=Decimal("1000000"),
        source="test",
    )


def _make_provider(
    name: str,
    *,
    supports: bool = True,
    result: list[OHLCVCandleSchema] | None = None,
    raises: Exception | None = None,
) -> MarketDataProvider:
    mock = MagicMock(spec=MarketDataProvider)
    mock.source_name = name
    mock.supports_timeframe.return_value = supports
    if raises is not None:
        mock.get_historical = AsyncMock(side_effect=raises)
    else:
        mock.get_historical = AsyncMock(return_value=result if result is not None else [])
    return mock


class TestProviderChainInit:
    def test_raises_on_empty_providers(self) -> None:
        with pytest.raises(ValueError, match="at least one provider"):
            ProviderChain([])

    def test_source_name_joins_all_providers(self) -> None:
        p1 = _make_provider("polygon")
        p2 = _make_provider("yfinance")
        chain = ProviderChain([p1, p2])
        assert chain.source_name == "polygon+yfinance"

    def test_supports_timeframe_true_if_any_provider_supports(self) -> None:
        p1 = _make_provider("a", supports=False)
        p2 = _make_provider("b", supports=True)
        assert ProviderChain([p1, p2]).supports_timeframe("1d") is True

    def test_supports_timeframe_false_if_none_support(self) -> None:
        p1 = _make_provider("a", supports=False)
        p2 = _make_provider("b", supports=False)
        assert ProviderChain([p1, p2]).supports_timeframe("4h") is False


class TestProviderChainGetHistorical:
    async def test_primary_success_returns_result(self) -> None:
        candles = [_candle()]
        p1 = _make_provider("primary", result=candles)
        p2 = _make_provider("fallback")
        chain = ProviderChain([p1, p2])

        start, end = _DATE_RANGE
        result = await chain.get_historical("AAPL", "1d", start, end)

        assert result == candles
        p2.get_historical.assert_not_called()

    async def test_primary_exception_falls_back_to_secondary(self) -> None:
        candles = [_candle()]
        p1 = _make_provider("primary", raises=RuntimeError("timeout"))
        p2 = _make_provider("fallback", result=candles)
        chain = ProviderChain([p1, p2])

        start, end = _DATE_RANGE
        result = await chain.get_historical("AAPL", "1d", start, end)

        assert result == candles
        p2.get_historical.assert_called_once()

    async def test_primary_empty_result_falls_back_to_secondary(self) -> None:
        candles = [_candle()]
        p1 = _make_provider("primary", result=[])
        p2 = _make_provider("fallback", result=candles)
        chain = ProviderChain([p1, p2])

        start, end = _DATE_RANGE
        result = await chain.get_historical("AAPL", "1d", start, end)

        assert result == candles

    async def test_all_fail_reraises_last_exception(self) -> None:
        exc = ConnectionError("network down")
        p1 = _make_provider("primary", raises=RuntimeError("timeout"))
        p2 = _make_provider("fallback", raises=exc)
        chain = ProviderChain([p1, p2])

        start, end = _DATE_RANGE
        with pytest.raises(ConnectionError, match="network down"):
            await chain.get_historical("AAPL", "1d", start, end)

    async def test_all_return_empty_returns_empty_list(self) -> None:
        p1 = _make_provider("primary", result=[])
        p2 = _make_provider("fallback", result=[])
        chain = ProviderChain([p1, p2])

        start, end = _DATE_RANGE
        result = await chain.get_historical("AAPL", "1d", start, end)

        assert result == []
        # Both providers tried.
        p1.get_historical.assert_called_once()
        p2.get_historical.assert_called_once()

    async def test_unsupported_timeframe_provider_skipped(self) -> None:
        candles = [_candle()]
        p1 = _make_provider("no-intraday", supports=False)
        p2 = _make_provider("has-intraday", supports=True, result=candles)
        chain = ProviderChain([p1, p2])

        start, end = _DATE_RANGE
        result = await chain.get_historical("AAPL", "1m", start, end)

        assert result == candles
        p1.get_historical.assert_not_called()
        p2.get_historical.assert_called_once()

    async def test_single_provider_success(self) -> None:
        candles = [_candle("TSLA")]
        p1 = _make_provider("only", result=candles)
        chain = ProviderChain([p1])

        start, end = _DATE_RANGE
        assert await chain.get_historical("TSLA", "1d", start, end) == candles

    async def test_single_provider_raises_propagates(self) -> None:
        p1 = _make_provider("only", raises=ValueError("bad symbol"))
        chain = ProviderChain([p1])

        start, end = _DATE_RANGE
        with pytest.raises(ValueError, match="bad symbol"):
            await chain.get_historical("???", "1d", start, end)

    async def test_three_providers_uses_third_after_two_fail(self) -> None:
        candles = [_candle("BTC")]
        p1 = _make_provider("p1", raises=RuntimeError("p1 down"))
        p2 = _make_provider("p2", raises=RuntimeError("p2 down"))
        p3 = _make_provider("p3", result=candles)
        chain = ProviderChain([p1, p2, p3])

        start, end = _DATE_RANGE
        result = await chain.get_historical("BTC", "1d", start, end)

        assert result == candles
        p3.get_historical.assert_called_once()
