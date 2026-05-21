import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.holding import Holding


class HoldingRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_portfolio_asset(
        self, portfolio_id: uuid.UUID, asset_id: uuid.UUID
    ) -> Holding | None:
        result = await self._session.execute(
            select(Holding).where(
                Holding.portfolio_id == portfolio_id,
                Holding.asset_id == asset_id,
            )
        )
        return result.scalar_one_or_none()

    async def create(
        self,
        portfolio_id: uuid.UUID,
        asset_id: uuid.UUID,
        symbol: str,
        quantity: float,
        avg_price: float,
    ) -> Holding:
        holding = Holding(
            portfolio_id=portfolio_id,
            asset_id=asset_id,
            symbol=symbol,
            quantity=quantity,
            avg_price=avg_price,
        )
        self._session.add(holding)
        await self._session.flush()
        return holding

    async def update(self, holding: Holding) -> Holding:
        # holding is already tracked by the session; flush persists in-place mutations
        await self._session.flush()
        return holding

    async def list_by_portfolio(self, portfolio_id: uuid.UUID) -> list[Holding]:
        result = await self._session.execute(
            select(Holding).where(Holding.portfolio_id == portfolio_id)
        )
        return list(result.scalars().all())

    async def delete(self, holding: Holding) -> None:
        await self._session.delete(holding)
        await self._session.flush()
