from __future__ import annotations

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies.auth import TokenData, get_current_user
from app.models.asset import Asset
from app.models.ohlcv import OHLCVCandle
from app.pipelines.ohlcv_pipeline import _detect_gaps
from app.providers.base import OHLCVCandleSchema
from app.schemas.market import APISuccess, CandleResponse
from app.services.indicators import VALID_INDICATORS, compute_indicators, validate_indicators

router = APIRouter(prefix="/api/v1/market", tags=["candles"])

_VALID_TIMEFRAMES = {"1m", "5m", "15m", "30m", "1h", "4h", "1d", "1w"}
_DEFAULT_LIMIT = 300
_MAX_LIMIT = 2000


@router.get("/candles", response_model=APISuccess[list[CandleResponse]])
async def get_candles(
    symbol: Annotated[str, Query(description="Asset symbol, e.g. RELIANCE")],
    timeframe: Annotated[str, Query(description="Candle timeframe")] = "1d",
    start: Annotated[datetime | None, Query()] = None,
    end: Annotated[datetime | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=_MAX_LIMIT)] = _DEFAULT_LIMIT,
    indicators: Annotated[
        str | None,
        Query(
            description=(
                f"Comma-separated indicator keys. Valid: {sorted(VALID_INDICATORS)}"
            )
        ),
    ] = None,
    db: AsyncSession = Depends(get_db),
    _user: TokenData = Depends(get_current_user),
) -> APISuccess[list[CandleResponse]]:
    """Return OHLCV candles for a symbol with optional server-side indicators."""
    if timeframe not in _VALID_TIMEFRAMES:
        raise HTTPException(
            status_code=422,
            detail={
                "code": "INVALID_TIMEFRAME",
                "message": f"timeframe must be one of {sorted(_VALID_TIMEFRAMES)}",
            },
        )

    indicator_list: list[str] = []
    if indicators:
        raw = [i.strip() for i in indicators.split(",") if i.strip()]
        try:
            indicator_list = validate_indicators(raw)
        except ValueError as exc:
            raise HTTPException(
                status_code=422,
                detail={"code": "INVALID_INDICATOR", "message": str(exc)},
            ) from exc

    asset_result = await db.execute(select(Asset).where(Asset.symbol == symbol.upper()))
    asset = asset_result.scalar_one_or_none()
    if asset is None:
        raise HTTPException(
            status_code=404,
            detail={"code": "NOT_FOUND", "message": f"Asset '{symbol}' not found"},
        )

    stmt = select(OHLCVCandle).where(
        OHLCVCandle.asset_id == asset.id,
        OHLCVCandle.timeframe == timeframe,
    )
    if start:
        stmt = stmt.where(OHLCVCandle.time >= start)
    if end:
        stmt = stmt.where(OHLCVCandle.time <= end)

    stmt = stmt.order_by(OHLCVCandle.time.desc()).limit(limit)
    result = await db.execute(stmt)
    candles = list(result.scalars().all())
    candles.sort(key=lambda c: c.time)

    ind_values = compute_indicators(candles, indicator_list)

    # Detect gaps in the returned slice so clients know if data is incomplete.
    gap_schemas = [
        OHLCVCandleSchema(
            time=c.time,
            symbol=symbol.upper(),
            timeframe=timeframe,
            open=c.open,
            high=c.high,
            low=c.low,
            close=c.close,
            volume=c.volume,
            vwap=c.vwap,
            trade_count=c.trade_count,
            source=c.source,
        )
        for c in candles
    ]
    asset_type: str = asset.asset_type or "equity"
    gaps_detected = _detect_gaps(gap_schemas, timeframe, symbol.upper(), asset_type)

    return APISuccess(
        data=[
            CandleResponse(
                time=c.time,
                open=float(c.open),
                high=float(c.high),
                low=float(c.low),
                close=float(c.close),
                volume=float(c.volume),
                indicators=ind_values[i],
            )
            for i, c in enumerate(candles)
        ],
        meta={"gaps_detected": gaps_detected},
    )
