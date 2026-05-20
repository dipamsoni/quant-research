from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies.auth import TokenData, get_current_user
from app.models.asset import Asset
from app.models.watchlist import WatchlistItem
from app.schemas.market import APISuccess, WatchlistAddRequest, WatchlistItemResponse

router = APIRouter(prefix="/api/v1/market", tags=["watchlist"])


@router.get("/watchlist", response_model=APISuccess[list[WatchlistItemResponse]])
async def get_watchlist(
    db: AsyncSession = Depends(get_db),
    user: TokenData = Depends(get_current_user),
) -> APISuccess[list[WatchlistItemResponse]]:
    result = await db.execute(
        select(WatchlistItem)
        .where(WatchlistItem.user_id == user.user_id)
        .order_by(WatchlistItem.added_at.desc())
    )
    items = list(result.scalars().all())
    return APISuccess(
        data=[
            WatchlistItemResponse(
                id=item.id,
                symbol=item.asset.symbol,
                name=item.asset.name,
                asset_type=item.asset.asset_type,
                exchange=item.asset.exchange,
                added_at=item.added_at,
            )
            for item in items
        ]
    )


@router.post("/watchlist", response_model=APISuccess[WatchlistItemResponse], status_code=201)
async def add_to_watchlist(
    payload: WatchlistAddRequest,
    db: AsyncSession = Depends(get_db),
    user: TokenData = Depends(get_current_user),
) -> APISuccess[WatchlistItemResponse]:
    asset_result = await db.execute(
        select(Asset).where(
            Asset.symbol == payload.symbol.upper(), Asset.is_active.is_(True)
        )
    )
    asset = asset_result.scalar_one_or_none()
    if asset is None:
        raise HTTPException(
            status_code=404,
            detail={"code": "NOT_FOUND", "message": f"Asset '{payload.symbol}' not found"},
        )

    existing = await db.execute(
        select(WatchlistItem).where(
            WatchlistItem.user_id == user.user_id,
            WatchlistItem.asset_id == asset.id,
        )
    )
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=409,
            detail={"code": "CONFLICT", "message": f"'{payload.symbol}' already in watchlist"},
        )

    item = WatchlistItem(user_id=user.user_id, asset_id=asset.id)
    db.add(item)
    await db.flush()
    await db.refresh(item)

    return APISuccess(
        data=WatchlistItemResponse(
            id=item.id,
            symbol=asset.symbol,
            name=asset.name,
            asset_type=asset.asset_type,
            exchange=asset.exchange,
            added_at=item.added_at,
        )
    )


@router.delete("/watchlist/{symbol}", response_model=APISuccess[None])
async def remove_from_watchlist(
    symbol: str,
    db: AsyncSession = Depends(get_db),
    user: TokenData = Depends(get_current_user),
) -> APISuccess[None]:
    asset_result = await db.execute(
        select(Asset).where(Asset.symbol == symbol.upper())
    )
    asset = asset_result.scalar_one_or_none()
    if asset is None:
        raise HTTPException(
            status_code=404,
            detail={"code": "NOT_FOUND", "message": f"Asset '{symbol}' not found"},
        )

    result = await db.execute(
        delete(WatchlistItem).where(
            WatchlistItem.user_id == user.user_id,
            WatchlistItem.asset_id == asset.id,
        )
    )
    if result.rowcount == 0:
        raise HTTPException(
            status_code=404,
            detail={"code": "NOT_FOUND", "message": f"'{symbol}' not in watchlist"},
        )

    return APISuccess(data=None)
