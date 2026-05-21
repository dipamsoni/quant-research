import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.transaction import Transaction


class TransactionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        portfolio_id: uuid.UUID,
        asset_id: uuid.UUID,
        transaction_type: str,
        quantity: Decimal,
        price: Decimal,
        fees: Decimal,
        executed_at: datetime,
    ) -> Transaction:
        tx = Transaction(
            portfolio_id=portfolio_id,
            asset_id=asset_id,
            transaction_type=transaction_type,
            quantity=quantity,
            price=price,
            fees=fees,
            executed_at=executed_at,
        )
        self._session.add(tx)
        await self._session.flush()
        return tx
