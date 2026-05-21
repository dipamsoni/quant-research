from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

import httpx
import structlog
from jose import jwt
from redis.asyncio import Redis

from app.core.config import settings

logger = structlog.get_logger()

NIFTY50_SYMBOL = "^NSEI"
_CACHE_TTL = 600  # 10 minutes


@dataclass
class PricePoint:
    date: date
    close: Decimal


class MarketDataClient:
    """Async HTTP client for market-data-service with Redis circuit-breaker fallback.

    Pass `redis` in tests to inject a mock. In production, the singleton from
    app.core.redis is resolved lazily at call time.
    """

    def __init__(
        self,
        base_url: str = settings.MARKET_DATA_SERVICE_URL,
        jwt_secret: str = settings.JWT_SECRET,
        jwt_algorithm: str = settings.JWT_ALGORITHM,
        token_exp_seconds: int = settings.INTERNAL_TOKEN_EXP_SECONDS,
        redis: Redis | None = None,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._jwt_secret = jwt_secret
        self._algorithm = jwt_algorithm
        self._token_exp_seconds = token_exp_seconds
        self._redis = redis

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_redis(self) -> Redis | None:
        if self._redis is not None:
            return self._redis
        try:
            from app.core.redis import get_redis
            return get_redis()
        except Exception:
            return None

    def _make_token(self) -> str:
        payload = {
            "sub": "portfolio-service",
            "exp": datetime.now(timezone.utc) + timedelta(seconds=self._token_exp_seconds),
        }
        return jwt.encode(payload, self._jwt_secret, algorithm=self._algorithm)

    def _auth_headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self._make_token()}"}

    async def _cache_read(self, key: str) -> str | None:
        redis = self._get_redis()
        if redis is None:
            return None
        try:
            return await redis.get(key)
        except Exception:
            return None

    async def _cache_write(self, key: str, value: str) -> None:
        redis = self._get_redis()
        if redis is None:
            return
        try:
            await redis.set(key, value, ex=_CACHE_TTL)
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def get_current_price(self, symbol: str) -> Decimal:
        """Latest price for symbol. Raises if both HTTP and Redis cache fail."""
        sym = symbol.upper()
        cache_key = f"portfolio:price:{sym}"

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(
                    f"{self._base_url}/api/v1/market/price/{sym}",
                    headers=self._auth_headers(),
                )
                resp.raise_for_status()
                price = Decimal(str(resp.json()["data"]["price"]))
            await self._cache_write(cache_key, str(price))
            return price
        except Exception:
            cached = await self._cache_read(cache_key)
            if cached:
                logger.warning("market_data_fallback_cache", symbol=sym, method="get_current_price")
                return Decimal(cached)
            raise

    async def get_price_history(
        self, symbol: str, from_date: date, to_date: date
    ) -> list[PricePoint]:
        """Daily close history in [from_date, to_date]. Returns [] if both HTTP and cache fail."""
        sym = symbol.upper()
        cache_key = f"portfolio:history:{sym}:{from_date}:{to_date}"

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(
                    f"{self._base_url}/api/v1/market/candles",
                    params={
                        "symbol": sym,
                        "timeframe": "1d",
                        "start": f"{from_date}T00:00:00",
                        "end": f"{to_date}T23:59:59",
                        "limit": 2000,
                    },
                    headers=self._auth_headers(),
                )
                resp.raise_for_status()
                candles: list[dict] = resp.json()["data"]
            points = [
                PricePoint(
                    date=datetime.fromisoformat(c["time"]).date(),
                    close=Decimal(str(c["close"])),
                )
                for c in candles
            ]
            serialized = json.dumps(
                [{"date": str(p.date), "close": str(p.close)} for p in points]
            )
            await self._cache_write(cache_key, serialized)
            return points
        except Exception:
            cached = await self._cache_read(cache_key)
            if cached:
                logger.warning("market_data_fallback_cache", symbol=sym, method="get_price_history")
                raw: list[dict] = json.loads(cached)
                return [
                    PricePoint(date=date.fromisoformat(r["date"]), close=Decimal(r["close"]))
                    for r in raw
                ]
            return []

    async def get_nifty50_history(
        self, from_date: date, to_date: date
    ) -> list[PricePoint]:
        """Nifty 50 benchmark daily closes in [from_date, to_date]."""
        return await self.get_price_history(NIFTY50_SYMBOL, from_date, to_date)

    # ------------------------------------------------------------------
    # Legacy — used by metrics.py; kept for backward compat
    # ------------------------------------------------------------------

    async def get_daily_closes(self, symbol: str, limit: int = 35) -> list[float]:
        """Return up to `limit` daily close prices for `symbol`, oldest first.

        Returns an empty list on any HTTP / network error so callers can
        degrade gracefully (missing prices → metrics become None rather than
        crashing the snapshot job).
        """
        token = self._make_token()
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(
                    f"{self._base_url}/api/v1/market/candles",
                    params={"symbol": symbol, "timeframe": "1d", "limit": limit},
                    headers={"Authorization": f"Bearer {token}"},
                )
                resp.raise_for_status()
                candles: list[dict] = resp.json()["data"]
                return [float(c["close"]) for c in candles]
        except Exception:
            return []
