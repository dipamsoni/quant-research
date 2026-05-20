from __future__ import annotations

import json
from datetime import datetime, timezone
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.redis import get_redis
from app.dependencies.auth import TokenData, get_current_user
from app.models.asset import Asset
from app.models.ohlcv import OHLCVCandle
from app.schemas.market import APISuccess, PriceResponse

router = APIRouter(prefix="/api/v1/market", tags=["price"])

_CACHE_TTL = 5  # seconds
_CACHE_KEY = "price:{symbol}"


def _cache_key(symbol: str) -> str:
    return _CACHE_KEY.format(symbol=symbol.upper())


@router.get("/price/{symbol}", response_model=APISuccess[PriceResponse])
async def get_price(
    symbol: str,
    db: AsyncSession = Depends(get_db),
    _user: TokenData = Depends(get_current_user),
) -> APISuccess[PriceResponse]:
    """Latest price for symbol. Redis cache with 5 s TTL; falls back to latest DB candle."""
    sym = symbol.upper()

    # 1. Redis cache hit
    try:
        redis = get_redis()
        cached = await redis.get(_cache_key(sym))
        if cached:
            data = json.loads(cached)
            return APISuccess(
                data=PriceResponse(
                    symbol=sym,
                    price=Decimal(data["price"]),
                    as_of=datetime.fromisoformat(data["as_of"]),
                )
            )
    except Exception:
        pass  # Redis unavailable — fall through to DB

    # 2. Asset existence check
    asset_result = await db.execute(select(Asset).where(Asset.symbol == sym))
    asset = asset_result.scalar_one_or_none()
    if asset is None:
        raise HTTPException(
            status_code=404,
            detail={"code": "NOT_FOUND", "message": f"Asset '{symbol}' not found"},
        )

    # 3. Latest close from any timeframe, most recent first
    candle_result = await db.execute(
        select(OHLCVCandle)
        .where(OHLCVCandle.asset_id == asset.id)
        .order_by(OHLCVCandle.time.desc())
        .limit(1)
    )
    candle = candle_result.scalar_one_or_none()
    if candle is None:
        raise HTTPException(
            status_code=404,
            detail={"code": "NO_DATA", "message": f"No price data for '{symbol}'"},
        )

    price = candle.close
    as_of = candle.time

    # 4. Write to Redis cache
    try:
        payload = json.dumps({"price": str(price), "as_of": as_of.isoformat()})
        await redis.set(_cache_key(sym), payload, ex=_CACHE_TTL)
    except Exception:
        pass

    return APISuccess(data=PriceResponse(symbol=sym, price=price, as_of=as_of))
