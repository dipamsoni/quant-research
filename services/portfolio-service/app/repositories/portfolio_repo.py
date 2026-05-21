import uuid
from decimal import Decimal

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.portfolio import Portfolio


class PortfolioRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        user_id: uuid.UUID,
        name: str,
        base_currency: str = "INR",
        risk_profile: str | None = None,
        initial_cash: Decimal = Decimal("0"),
    ) -> Portfolio:
        portfolio = Portfolio(
            user_id=user_id,
            name=name,
            base_currency=base_currency,
            risk_profile=risk_profile,
            cash_balance=initial_cash,
        )
        self._session.add(portfolio)
        await self._session.flush()
        return portfolio

    async def get_by_id(self, portfolio_id: uuid.UUID) -> Portfolio | None:
        result = await self._session.execute(
            select(Portfolio).where(Portfolio.id == portfolio_id)
        )
        return result.scalar_one_or_none()

    async def list_by_user(self, user_id: uuid.UUID) -> list[Portfolio]:
        result = await self._session.execute(
            select(Portfolio).where(Portfolio.user_id == user_id).order_by(Portfolio.created_at)
        )
        return list(result.scalars().all())

    async def delete(self, portfolio_id: uuid.UUID) -> bool:
        result = await self._session.execute(
            delete(Portfolio).where(Portfolio.id == portfolio_id)
        )
        return result.rowcount > 0
