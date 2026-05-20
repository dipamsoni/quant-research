"""Unit tests for market REST endpoints.

Uses FastAPI test client with overridden DB and Redis dependencies —
no real infrastructure required.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.core.database import get_db
from app.dependencies.auth import TokenData, get_current_user
from app.main import app
from app.models.asset import Asset
from app.models.ohlcv import OHLCVCandle


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _asset(
    symbol: str = "RELIANCE",
    name: str = "Reliance Industries Ltd",
    asset_type: str = "stock",
) -> Asset:
    a = Asset()
    a.id = uuid.uuid4()
    a.symbol = symbol
    a.name = name
    a.asset_type = asset_type
    a.exchange = "NSE"
    a.currency = "INR"
    a.sector = "Energy"
    a.industry = "Oil & Gas Refining"
    a.is_active = True
    a.created_at = datetime(2024, 1, 1, tzinfo=timezone.utc)
    return a


def _candle(asset_id: uuid.UUID, close: str = "185.00000000") -> OHLCVCandle:
    c = OHLCVCandle()
    c.time = datetime(2024, 6, 1, tzinfo=timezone.utc)
    c.asset_id = asset_id
    c.timeframe = "1d"
    c.open = Decimal("180.00000000")
    c.high = Decimal("190.00000000")
    c.low = Decimal("179.00000000")
    c.close = Decimal(close)
    c.volume = Decimal("50000000.00000000")
    c.vwap = None
    c.trade_count = None
    c.source = "yfinance"
    return c


def _stub_auth() -> TokenData:
    return TokenData(user_id="user-1", email="test@example.com", role="user")


_UNSET = object()


def _make_db_mock(scalars_return: object = _UNSET, scalar_one_or_none_return: object = _UNSET) -> AsyncMock:
    """Build an AsyncSession mock that returns given value from execute."""
    execute_result = MagicMock()
    if scalars_return is not _UNSET:
        scalars_mock = MagicMock()
        scalars_mock.all.return_value = scalars_return
        execute_result.scalars.return_value = scalars_mock
    if scalar_one_or_none_return is not _UNSET:
        execute_result.scalar_one_or_none.return_value = scalar_one_or_none_return
    db = AsyncMock()
    db.execute = AsyncMock(return_value=execute_result)
    return db


@pytest.fixture(autouse=True)
def override_auth() -> None:
    app.dependency_overrides[get_current_user] = _stub_auth
    yield
    app.dependency_overrides.pop(get_current_user, None)


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


# ---------------------------------------------------------------------------
# /api/v1/market/assets
# ---------------------------------------------------------------------------


class TestListAssets:
    def test_returns_assets(self, client: TestClient) -> None:
        assets = [_asset("RELIANCE"), _asset("TCS", "Tata Consultancy Services")]
        db = _make_db_mock(scalars_return=assets)
        app.dependency_overrides[get_db] = lambda: (x for x in [db])  # type: ignore[assignment]

        with patch("app.api.v1.assets.get_db", return_value=db):
            # Re-override with an async generator
            async def _get_db_override():  # type: ignore[no-untyped-def]
                yield db
            app.dependency_overrides[get_db] = _get_db_override

            res = client.get("/api/v1/market/assets")

        app.dependency_overrides.pop(get_db, None)
        assert res.status_code == 200
        data = res.json()["data"]
        assert len(data) == 2
        assert data[0]["symbol"] == "RELIANCE"

    def test_cursor_pagination(self, client: TestClient) -> None:
        # Returns limit+1 assets → has_more=True, next_cursor set
        assets = [_asset(f"SYM{i:02d}") for i in range(51)]
        db = _make_db_mock(scalars_return=assets)

        async def _get_db_override():  # type: ignore[no-untyped-def]
            yield db
        app.dependency_overrides[get_db] = _get_db_override

        res = client.get("/api/v1/market/assets?limit=50")
        app.dependency_overrides.pop(get_db, None)

        assert res.status_code == 200
        body = res.json()
        assert body["pagination"]["has_more"] is True
        assert body["pagination"]["next_cursor"] == "SYM49"
        assert len(body["data"]) == 50


class TestGetAsset:
    def test_404_when_not_found(self, client: TestClient) -> None:
        db = _make_db_mock(scalar_one_or_none_return=None)

        async def _get_db_override():  # type: ignore[no-untyped-def]
            yield db
        app.dependency_overrides[get_db] = _get_db_override

        with patch("app.api.v1.assets.get_redis", side_effect=RuntimeError("no redis")):
            res = client.get("/api/v1/market/assets/FAKE")

        app.dependency_overrides.pop(get_db, None)
        assert res.status_code == 404

    def test_returns_asset_with_price_from_db(self, client: TestClient) -> None:
        asset = _asset()
        candle = _candle(asset.id, "185.50")

        execute_result_asset = MagicMock()
        execute_result_asset.scalar_one_or_none.return_value = asset

        execute_result_candle = MagicMock()
        execute_result_candle.scalar_one_or_none.return_value = candle

        db = AsyncMock()
        db.execute = AsyncMock(
            side_effect=[execute_result_asset, execute_result_candle]
        )

        async def _get_db_override():  # type: ignore[no-untyped-def]
            yield db
        app.dependency_overrides[get_db] = _get_db_override

        with patch("app.api.v1.assets.get_redis", side_effect=RuntimeError("no redis")):
            res = client.get("/api/v1/market/assets/RELIANCE")

        app.dependency_overrides.pop(get_db, None)
        assert res.status_code == 200
        data = res.json()["data"]
        assert data["symbol"] == "RELIANCE"
        assert data["price"] == "185.50"


# ---------------------------------------------------------------------------
# /api/v1/market/candles
# ---------------------------------------------------------------------------


class TestGetCandles:
    def test_404_when_asset_not_found(self, client: TestClient) -> None:
        db = _make_db_mock(scalar_one_or_none_return=None)

        async def _get_db_override():  # type: ignore[no-untyped-def]
            yield db
        app.dependency_overrides[get_db] = _get_db_override

        res = client.get("/api/v1/market/candles?symbol=FAKE&timeframe=1d")
        app.dependency_overrides.pop(get_db, None)
        assert res.status_code == 404

    def test_invalid_timeframe_returns_422(self, client: TestClient) -> None:
        res = client.get("/api/v1/market/candles?symbol=RELIANCE&timeframe=3d")
        assert res.status_code == 422

    def test_returns_candles_ascending(self, client: TestClient) -> None:
        asset = _asset()
        c1 = _candle(asset.id, "180.00000000")
        c1.time = datetime(2024, 6, 1, tzinfo=timezone.utc)
        c2 = _candle(asset.id, "185.00000000")
        c2.time = datetime(2024, 6, 2, tzinfo=timezone.utc)

        execute_asset = MagicMock()
        execute_asset.scalar_one_or_none.return_value = asset

        execute_candles = MagicMock()
        scalars_mock = MagicMock()
        scalars_mock.all.return_value = [c2, c1]  # DESC from DB, should be sorted ASC
        execute_candles.scalars.return_value = scalars_mock

        db = AsyncMock()
        db.execute = AsyncMock(side_effect=[execute_asset, execute_candles])

        async def _get_db_override():  # type: ignore[no-untyped-def]
            yield db
        app.dependency_overrides[get_db] = _get_db_override

        res = client.get("/api/v1/market/candles?symbol=RELIANCE&timeframe=1d")
        app.dependency_overrides.pop(get_db, None)

        assert res.status_code == 200
        data = res.json()["data"]
        assert len(data) == 2
        assert data[0]["close"] == 180.0
        assert data[1]["close"] == 185.0


# ---------------------------------------------------------------------------
# /api/v1/market/price/{symbol}
# ---------------------------------------------------------------------------


class TestGetPrice:
    def test_returns_price_from_redis_cache(self, client: TestClient) -> None:
        cached = json.dumps(
            {"price": "185.50", "as_of": "2024-06-01T12:00:00+00:00"}
        )
        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value=cached)

        with patch("app.api.v1.price.get_redis", return_value=mock_redis):
            res = client.get("/api/v1/market/price/RELIANCE")

        assert res.status_code == 200
        data = res.json()["data"]
        assert data["symbol"] == "RELIANCE"
        assert data["price"] == "185.50"

    def test_falls_back_to_db_on_cache_miss(self, client: TestClient) -> None:
        asset = _asset()
        candle = _candle(asset.id, "190.00000000")

        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value=None)
        mock_redis.set = AsyncMock()

        execute_asset = MagicMock()
        execute_asset.scalar_one_or_none.return_value = asset

        execute_candle = MagicMock()
        execute_candle.scalar_one_or_none.return_value = candle

        db = AsyncMock()
        db.execute = AsyncMock(side_effect=[execute_asset, execute_candle])

        async def _get_db_override():  # type: ignore[no-untyped-def]
            yield db
        app.dependency_overrides[get_db] = _get_db_override

        with patch("app.api.v1.price.get_redis", return_value=mock_redis):
            res = client.get("/api/v1/market/price/RELIANCE")

        app.dependency_overrides.pop(get_db, None)
        assert res.status_code == 200
        assert res.json()["data"]["price"] == "190.00000000"

    def test_writes_cache_on_db_hit(self, client: TestClient) -> None:
        asset = _asset()
        candle = _candle(asset.id, "200.0")

        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value=None)
        mock_redis.set = AsyncMock()

        execute_asset = MagicMock()
        execute_asset.scalar_one_or_none.return_value = asset

        execute_candle = MagicMock()
        execute_candle.scalar_one_or_none.return_value = candle

        db = AsyncMock()
        db.execute = AsyncMock(side_effect=[execute_asset, execute_candle])

        async def _get_db_override():  # type: ignore[no-untyped-def]
            yield db
        app.dependency_overrides[get_db] = _get_db_override

        with patch("app.api.v1.price.get_redis", return_value=mock_redis):
            client.get("/api/v1/market/price/RELIANCE")

        app.dependency_overrides.pop(get_db, None)
        mock_redis.set.assert_awaited_once()
        call_kwargs = mock_redis.set.call_args
        assert call_kwargs[1]["ex"] == 5

    def test_404_when_no_data(self, client: TestClient) -> None:
        asset = _asset()
        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value=None)
        mock_redis.set = AsyncMock()

        execute_asset = MagicMock()
        execute_asset.scalar_one_or_none.return_value = asset

        execute_candle = MagicMock()
        execute_candle.scalar_one_or_none.return_value = None

        db = AsyncMock()
        db.execute = AsyncMock(side_effect=[execute_asset, execute_candle])

        async def _get_db_override():  # type: ignore[no-untyped-def]
            yield db
        app.dependency_overrides[get_db] = _get_db_override

        with patch("app.api.v1.price.get_redis", return_value=mock_redis):
            res = client.get("/api/v1/market/price/RELIANCE")

        app.dependency_overrides.pop(get_db, None)
        assert res.status_code == 404
        assert res.json()["error"]["code"] == "NO_DATA"
