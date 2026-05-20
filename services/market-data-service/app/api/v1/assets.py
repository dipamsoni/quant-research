from __future__ import annotations

import json
from datetime import datetime, timezone
from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.redis import get_redis
from app.dependencies.auth import TokenData, get_current_user
from app.models.asset import Asset
from app.models.ohlcv import OHLCVCandle
from app.schemas.market import APISuccess, AssetDetailResponse, AssetResponse, Pagination

router = APIRouter(prefix="/api/v1/market", tags=["assets"])

_PAGE_SIZE = 50
_PRICE_CACHE_TTL = 5  # seconds


@router.get("/assets", response_model=APISuccess[list[AssetResponse]])
async def list_assets(
    search: Annotated[str | None, Query(max_length=100)] = None,
    type: Annotated[str | None, Query(alias="type")] = None,
    cursor: Annotated[str | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=200)] = _PAGE_SIZE,
    db: AsyncSession = Depends(get_db),
    _user: TokenData = Depends(get_current_user),
) -> APISuccess[list[AssetResponse]]:
    """Paginated asset list. Cursor is the last symbol received."""
    stmt = select(Asset).where(Asset.is_active.is_(True))

    if search:
        pattern = f"%{search}%"
        stmt = stmt.where(
            or_(
                func.lower(Asset.symbol).like(func.lower(pattern)),
                func.lower(Asset.name).like(func.lower(pattern)),
            )
        )
    if type:
        stmt = stmt.where(Asset.asset_type == type)
    if cursor:
        stmt = stmt.where(Asset.symbol > cursor)

    stmt = stmt.order_by(Asset.symbol).limit(limit + 1)
    result = await db.execute(stmt)
    rows = list(result.scalars().all())

    has_more = len(rows) > limit
    page = rows[:limit]
    next_cursor = page[-1].symbol if has_more and page else None

    return APISuccess(
        data=[AssetResponse.model_validate(a) for a in page],
        pagination=Pagination(next_cursor=next_cursor, has_more=has_more),
    )


@router.get("/assets/{symbol}", response_model=APISuccess[AssetDetailResponse])
async def get_asset(
    symbol: str,
    db: AsyncSession = Depends(get_db),
    _user: TokenData = Depends(get_current_user),
) -> APISuccess[AssetDetailResponse]:
    """Asset detail with latest price from Redis cache (falls back to DB)."""
    result = await db.execute(select(Asset).where(Asset.symbol == symbol.upper()))
    asset = result.scalar_one_or_none()
    if asset is None:
        raise HTTPException(
            status_code=404,
            detail={"code": "NOT_FOUND", "message": f"Asset '{symbol}' not found"},
        )

    price: Decimal | None = None
    as_of: datetime | None = None

    try:
        redis = get_redis()
        cached = await redis.get(f"price:{symbol.upper()}")
        if cached:
            data = json.loads(cached)
            price = Decimal(data["price"])
            as_of = datetime.fromisoformat(data["as_of"])
    except Exception:
        pass  # Redis unavailable — skip price enrichment

    if price is None:
        # Fall back to latest daily close from DB
        candle_result = await db.execute(
            select(OHLCVCandle)
            .where(OHLCVCandle.asset_id == asset.id, OHLCVCandle.timeframe == "1d")
            .order_by(OHLCVCandle.time.desc())
            .limit(1)
        )
        latest = candle_result.scalar_one_or_none()
        if latest:
            price = latest.close
            as_of = latest.time

    resp = AssetDetailResponse.model_validate(asset)
    resp = resp.model_copy(update={"price": price, "as_of": as_of})
    return APISuccess(data=resp)
