"""Integration tests for MarketDataClient — httpx and Redis are fully mocked."""
from __future__ import annotations

import json
from datetime import date
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.clients.market_data import MarketDataClient, PricePoint


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_redis() -> AsyncMock:
    redis = AsyncMock()
    redis.get.return_value = None  # cache miss by default
    redis.set.return_value = True
    return redis


@pytest.fixture
def client(mock_redis: AsyncMock) -> MarketDataClient:
    return MarketDataClient(
        base_url="http://test-market:8001",
        jwt_secret="test-secret",
        redis=mock_redis,
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_response(json_body: dict) -> MagicMock:
    resp = MagicMock()
    resp.json.return_value = json_body
    resp.raise_for_status = MagicMock()
    return resp


def _make_http_ctx(*, response: MagicMock | None = None, get_error: Exception | None = None) -> MagicMock:
    """Mock for `async with httpx.AsyncClient(...) as client:`."""
    mock_http = AsyncMock()
    if get_error:
        mock_http.get.side_effect = get_error
    else:
        mock_http.get.return_value = response
    ctx = MagicMock()
    ctx.__aenter__ = AsyncMock(return_value=mock_http)
    ctx.__aexit__ = AsyncMock(return_value=None)
    return ctx


# ---------------------------------------------------------------------------
# get_current_price
# ---------------------------------------------------------------------------


class TestGetCurrentPrice:
    async def test_success_returns_decimal(self, client: MarketDataClient, mock_redis: AsyncMock) -> None:
        resp = _make_response({"data": {"price": "2750.50", "as_of": "2026-05-20T10:00:00"}})
        ctx = _make_http_ctx(response=resp)

        with patch("httpx.AsyncClient", return_value=ctx):
            price = await client.get_current_price("RELIANCE")

        assert price == Decimal("2750.50")

    async def test_symbol_normalized_to_upper(self, client: MarketDataClient, mock_redis: AsyncMock) -> None:
        resp = _make_response({"data": {"price": "100.00", "as_of": "2026-05-20T10:00:00"}})
        ctx = _make_http_ctx(response=resp)

        with patch("httpx.AsyncClient", return_value=ctx):
            price = await client.get_current_price("reliance")

        assert price == Decimal("100.00")
        # Verify URL contained uppercased symbol
        call_url = ctx.__aenter__.return_value.get.call_args[0][0]
        assert "RELIANCE" in call_url

    async def test_caches_successful_response(self, client: MarketDataClient, mock_redis: AsyncMock) -> None:
        resp = _make_response({"data": {"price": "2750.50", "as_of": "2026-05-20T10:00:00"}})
        ctx = _make_http_ctx(response=resp)

        with patch("httpx.AsyncClient", return_value=ctx):
            await client.get_current_price("RELIANCE")

        mock_redis.set.assert_called_once()
        cache_key = mock_redis.set.call_args[0][0]
        assert cache_key == "portfolio:price:RELIANCE"

    async def test_circuit_breaker_uses_redis_on_http_error(
        self, client: MarketDataClient, mock_redis: AsyncMock
    ) -> None:
        mock_redis.get.return_value = "2750.50"
        ctx = _make_http_ctx(get_error=Exception("Connection refused"))

        with patch("httpx.AsyncClient", return_value=ctx):
            price = await client.get_current_price("RELIANCE")

        assert price == Decimal("2750.50")
        mock_redis.set.assert_not_called()

    async def test_raises_when_http_fails_and_cache_empty(
        self, client: MarketDataClient, mock_redis: AsyncMock
    ) -> None:
        mock_redis.get.return_value = None
        ctx = _make_http_ctx(get_error=Exception("timeout"))

        with patch("httpx.AsyncClient", return_value=ctx):
            with pytest.raises(Exception, match="timeout"):
                await client.get_current_price("RELIANCE")


# ---------------------------------------------------------------------------
# get_price_history
# ---------------------------------------------------------------------------


def _candle_body(n: int = 3, base_close: float = 100.0) -> dict:
    return {
        "data": [
            {"time": f"2026-05-{17 + i:02d}T00:00:00", "close": str(base_close + i)}
            for i in range(n)
        ]
    }


class TestGetPriceHistory:
    async def test_success_returns_price_points(
        self, client: MarketDataClient, mock_redis: AsyncMock
    ) -> None:
        resp = _make_response(_candle_body(3))
        ctx = _make_http_ctx(response=resp)

        with patch("httpx.AsyncClient", return_value=ctx):
            pts = await client.get_price_history("RELIANCE", date(2026, 5, 17), date(2026, 5, 19))

        assert len(pts) == 3
        assert all(isinstance(p, PricePoint) for p in pts)
        assert pts[0].close == Decimal("100.0")
        assert pts[0].date == date(2026, 5, 17)
        assert pts[2].close == Decimal("102.0")

    async def test_caches_successful_response(
        self, client: MarketDataClient, mock_redis: AsyncMock
    ) -> None:
        resp = _make_response(_candle_body(2))
        ctx = _make_http_ctx(response=resp)

        with patch("httpx.AsyncClient", return_value=ctx):
            await client.get_price_history("RELIANCE", date(2026, 5, 17), date(2026, 5, 18))

        mock_redis.set.assert_called_once()
        cache_key = mock_redis.set.call_args[0][0]
        assert cache_key == "portfolio:history:RELIANCE:2026-05-17:2026-05-18"

    async def test_circuit_breaker_uses_redis_on_http_error(
        self, client: MarketDataClient, mock_redis: AsyncMock
    ) -> None:
        cached_data = json.dumps([
            {"date": "2026-05-17", "close": "100.0"},
            {"date": "2026-05-18", "close": "101.0"},
        ])
        mock_redis.get.return_value = cached_data
        ctx = _make_http_ctx(get_error=Exception("timeout"))

        with patch("httpx.AsyncClient", return_value=ctx):
            pts = await client.get_price_history("RELIANCE", date(2026, 5, 17), date(2026, 5, 18))

        assert len(pts) == 2
        assert pts[0].date == date(2026, 5, 17)
        assert pts[1].close == Decimal("101.0")
        mock_redis.set.assert_not_called()

    async def test_returns_empty_when_http_fails_and_cache_empty(
        self, client: MarketDataClient, mock_redis: AsyncMock
    ) -> None:
        mock_redis.get.return_value = None
        ctx = _make_http_ctx(get_error=Exception("timeout"))

        with patch("httpx.AsyncClient", return_value=ctx):
            pts = await client.get_price_history("RELIANCE", date(2026, 5, 17), date(2026, 5, 19))

        assert pts == []

    async def test_uses_1d_timeframe_and_correct_date_params(
        self, client: MarketDataClient, mock_redis: AsyncMock
    ) -> None:
        resp = _make_response({"data": []})
        ctx = _make_http_ctx(response=resp)

        with patch("httpx.AsyncClient", return_value=ctx):
            await client.get_price_history("TCS", date(2026, 1, 1), date(2026, 1, 31))

        call_kwargs = ctx.__aenter__.return_value.get.call_args[1]
        params = call_kwargs["params"]
        assert params["timeframe"] == "1d"
        assert params["start"] == "2026-01-01T00:00:00"
        assert params["end"] == "2026-01-31T23:59:59"
        assert params["symbol"] == "TCS"


# ---------------------------------------------------------------------------
# get_nifty50_history
# ---------------------------------------------------------------------------


class TestGetNifty50History:
    async def test_delegates_to_price_history_with_nsei_symbol(
        self, client: MarketDataClient, mock_redis: AsyncMock
    ) -> None:
        resp = _make_response({"data": [{"time": "2026-05-19T00:00:00", "close": "22000.0"}]})
        ctx = _make_http_ctx(response=resp)

        with patch("httpx.AsyncClient", return_value=ctx):
            pts = await client.get_nifty50_history(date(2026, 5, 19), date(2026, 5, 19))

        assert len(pts) == 1
        assert pts[0].close == Decimal("22000.0")
        call_kwargs = ctx.__aenter__.return_value.get.call_args[1]
        assert call_kwargs["params"]["symbol"] == "^NSEI"

    async def test_returns_empty_on_total_failure(
        self, client: MarketDataClient, mock_redis: AsyncMock
    ) -> None:
        mock_redis.get.return_value = None
        ctx = _make_http_ctx(get_error=Exception("unreachable"))

        with patch("httpx.AsyncClient", return_value=ctx):
            pts = await client.get_nifty50_history(date(2026, 5, 1), date(2026, 5, 19))

        assert pts == []


# ---------------------------------------------------------------------------
# get_daily_closes (legacy)
# ---------------------------------------------------------------------------


class TestGetDailyCloses:
    async def test_returns_float_list(self, client: MarketDataClient, mock_redis: AsyncMock) -> None:
        resp = _make_response({"data": [{"close": 100.0}, {"close": 101.5}, {"close": 102.0}]})
        ctx = _make_http_ctx(response=resp)

        with patch("httpx.AsyncClient", return_value=ctx):
            closes = await client.get_daily_closes("RELIANCE", limit=3)

        assert closes == [100.0, 101.5, 102.0]

    async def test_returns_empty_list_on_error(
        self, client: MarketDataClient, mock_redis: AsyncMock
    ) -> None:
        ctx = _make_http_ctx(get_error=Exception("network error"))

        with patch("httpx.AsyncClient", return_value=ctx):
            closes = await client.get_daily_closes("RELIANCE")

        assert closes == []
