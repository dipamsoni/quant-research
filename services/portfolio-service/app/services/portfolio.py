import uuid
from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.portfolio import Portfolio
from app.repositories.portfolio_repo import PortfolioRepository


async def create_portfolio(
    session: AsyncSession,
    *,
    user_id: uuid.UUID,
    name: str,
    base_currency: str = "INR",
    risk_profile: str | None = None,
    initial_cash: Decimal = Decimal("0"),
) -> Portfolio:
    repo = PortfolioRepository(session)
    portfolio = await repo.create(
        user_id=user_id,
        name=name,
        base_currency=base_currency,
        risk_profile=risk_profile,
        initial_cash=initial_cash,
    )
    await session.commit()
    return portfolio


async def get_portfolio(
    session: AsyncSession,
    portfolio_id: uuid.UUID,
) -> Portfolio | None:
    repo = PortfolioRepository(session)
    return await repo.get_by_id(portfolio_id)


async def list_portfolios(
    session: AsyncSession,
    user_id: uuid.UUID,
) -> list[Portfolio]:
    repo = PortfolioRepository(session)
    return await repo.list_by_user(user_id)


async def get_portfolio_for_user(
    session: AsyncSession,
    portfolio_id: uuid.UUID,
    user_id: uuid.UUID,
) -> Portfolio:
    """Fetch portfolio and assert ownership. Raises 404 or 403 on failure."""
    portfolio = await get_portfolio(session, portfolio_id)
    if portfolio is None:
        raise HTTPException(
            status_code=404,
            detail={"code": "NOT_FOUND", "message": "Portfolio not found"},
        )
    if portfolio.user_id != user_id:
        raise HTTPException(
            status_code=403,
            detail={"code": "FORBIDDEN", "message": "Access denied"},
        )
    return portfolio


async def delete_portfolio(
    session: AsyncSession,
    portfolio_id: uuid.UUID,
) -> bool:
    repo = PortfolioRepository(session)
    deleted = await repo.delete(portfolio_id)
    if deleted:
        await session.commit()
    return deleted
