from __future__ import annotations

import uuid
from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies.auth import TokenData, get_current_user
from app.repositories.holding_repo import HoldingRepository
from app.repositories.portfolio_metrics_repo import PortfolioMetricsRepository
from app.schemas import (
    AllocationItem,
    AllocationResponse,
    APISuccess,
    HoldingResponse,
    MetricsSnapshotResponse,
    PortfolioCreate,
    PortfolioDetailResponse,
    PortfolioResponse,
    TransactionCreate,
    TransactionResponse,
)
from app.services.portfolio import (
    create_portfolio,
    get_portfolio_for_user,
    list_portfolios,
)
from app.services.transactions import record_transaction

router = APIRouter(prefix="/api/v1/portfolio", tags=["portfolio"])


@router.post("", response_model=APISuccess[PortfolioResponse], status_code=201)
async def create(
    body: PortfolioCreate,
    user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APISuccess[PortfolioResponse]:
    portfolio = await create_portfolio(
        db,
        user_id=uuid.UUID(user.user_id),
        name=body.name,
        base_currency=body.base_currency,
        risk_profile=body.risk_profile,
        initial_cash=body.initial_cash,
    )
    return APISuccess(data=PortfolioResponse.model_validate(portfolio))


@router.get("", response_model=APISuccess[list[PortfolioResponse]])
async def list_user_portfolios(
    user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APISuccess[list[PortfolioResponse]]:
    portfolios = await list_portfolios(db, user_id=uuid.UUID(user.user_id))
    return APISuccess(data=[PortfolioResponse.model_validate(p) for p in portfolios])


@router.get("/{portfolio_id}", response_model=APISuccess[PortfolioDetailResponse])
async def get_portfolio_detail(
    portfolio_id: uuid.UUID,
    user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APISuccess[PortfolioDetailResponse]:
    portfolio = await get_portfolio_for_user(db, portfolio_id, uuid.UUID(user.user_id))

    holding_repo = HoldingRepository(db)
    holdings = await holding_repo.list_by_portfolio(portfolio_id)

    metrics_repo = PortfolioMetricsRepository(db)
    latest = await metrics_repo.get_latest(portfolio_id)

    base = PortfolioResponse.model_validate(portfolio)
    detail = PortfolioDetailResponse(
        **base.model_dump(),
        holdings=[HoldingResponse.model_validate(h) for h in holdings],
        latest_metrics=MetricsSnapshotResponse.model_validate(latest) if latest else None,
    )
    return APISuccess(data=detail)


@router.post(
    "/{portfolio_id}/transactions",
    response_model=APISuccess[TransactionResponse],
    status_code=201,
)
async def add_transaction(
    portfolio_id: uuid.UUID,
    body: TransactionCreate,
    user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APISuccess[TransactionResponse]:
    await get_portfolio_for_user(db, portfolio_id, uuid.UUID(user.user_id))

    result = await record_transaction(
        db,
        portfolio_id=portfolio_id,
        asset_id=body.asset_id,
        symbol=body.symbol,
        transaction_type=body.transaction_type,
        quantity=body.quantity,
        price=body.price,
        fees=body.fees,
        executed_at=body.executed_at,
    )
    resp = TransactionResponse.model_validate(result.transaction).model_copy(
        update={"realized_pnl": result.realized_pnl}
    )
    return APISuccess(data=resp)


@router.get("/{portfolio_id}/metrics", response_model=APISuccess[list[MetricsSnapshotResponse]])
async def get_metrics(
    portfolio_id: uuid.UUID,
    from_date: Annotated[date | None, Query(alias="from")] = None,
    to_date: Annotated[date | None, Query(alias="to")] = None,
    user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APISuccess[list[MetricsSnapshotResponse]]:
    await get_portfolio_for_user(db, portfolio_id, uuid.UUID(user.user_id))

    effective_from = from_date or date.min
    effective_to = to_date or date.today()

    metrics_repo = PortfolioMetricsRepository(db)
    rows = await metrics_repo.list_range(portfolio_id, effective_from, effective_to)
    return APISuccess(data=[MetricsSnapshotResponse.model_validate(r) for r in rows])


@router.get("/{portfolio_id}/allocation", response_model=APISuccess[AllocationResponse])
async def get_allocation(
    portfolio_id: uuid.UUID,
    user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APISuccess[AllocationResponse]:
    await get_portfolio_for_user(db, portfolio_id, uuid.UUID(user.user_id))

    holding_repo = HoldingRepository(db)
    holdings = await holding_repo.list_by_portfolio(portfolio_id)

    # Prefer market_value set by snapshot job; fall back to cost basis
    items = [
        (
            h.asset_id,
            float(h.market_value)
            if h.market_value is not None
            else float(h.quantity) * float(h.avg_price),
        )
        for h in holdings
    ]
    total_value = sum(v for _, v in items)

    allocations = [
        AllocationItem(
            asset_id=asset_id,
            value=value,
            pct=round(value / total_value * 100, 4) if total_value > 0 else 0.0,
        )
        for asset_id, value in sorted(items, key=lambda x: x[1], reverse=True)
    ]
    return APISuccess(data=AllocationResponse(total_value=total_value, allocations=allocations))
