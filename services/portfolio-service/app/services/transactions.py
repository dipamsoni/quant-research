import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.holding import Holding
from app.models.portfolio import Portfolio
from app.models.transaction import Transaction
from app.repositories.holding_repo import HoldingRepository
from app.repositories.transaction_repo import TransactionRepository


def compute_avg_price(
    old_qty: Decimal,
    old_avg: Decimal,
    buy_qty: Decimal,
    buy_price: Decimal,
) -> Decimal:
    """Weighted average cost basis after buying into an existing position."""
    return (old_qty * old_avg + buy_qty * buy_price) / (old_qty + buy_qty)


def compute_realized_pnl(
    avg_price: Decimal,
    sell_price: Decimal,
    qty_sold: Decimal,
) -> Decimal:
    """Realized PnL for a SELL: positive = profit, negative = loss."""
    return (sell_price - avg_price) * qty_sold


@dataclass
class TransactionResult:
    transaction: Transaction
    holding: Holding | None  # None when the position was fully closed
    realized_pnl: Decimal


async def record_transaction(
    session: AsyncSession,
    *,
    portfolio_id: uuid.UUID,
    asset_id: uuid.UUID,
    symbol: str,
    transaction_type: str,
    quantity: Decimal,
    price: Decimal,
    fees: Decimal = Decimal("0"),
    executed_at: datetime | None = None,
) -> TransactionResult:
    if executed_at is None:
        executed_at = datetime.now(tz=timezone.utc)

    tx_type = transaction_type.lower()
    if tx_type not in ("buy", "sell"):
        raise HTTPException(
            status_code=422,
            detail={
                "code": "INVALID_TRANSACTION_TYPE",
                "message": "transaction_type must be 'buy' or 'sell'",
            },
        )

    holding_repo = HoldingRepository(session)
    tx_repo = TransactionRepository(session)

    existing = await holding_repo.get_by_portfolio_asset(portfolio_id, asset_id)
    realized_pnl = Decimal("0")
    holding: Holding | None

    if tx_type == "buy":
        if existing is None:
            holding = await holding_repo.create(
                portfolio_id=portfolio_id,
                asset_id=asset_id,
                symbol=symbol.upper(),
                quantity=float(quantity),
                avg_price=float(price),
            )
        else:
            old_qty = Decimal(str(existing.quantity))
            old_avg = Decimal(str(existing.avg_price))
            new_avg = compute_avg_price(old_qty, old_avg, quantity, price)
            existing.quantity = float(old_qty + quantity)
            existing.avg_price = float(new_avg)
            holding = await holding_repo.update(existing)

    else:  # sell
        held = Decimal(str(existing.quantity)) if existing is not None else Decimal("0")
        if existing is None or held < quantity:
            raise HTTPException(
                status_code=422,
                detail={
                    "code": "INSUFFICIENT_QUANTITY",
                    "message": f"cannot sell {quantity}; only {held} held",
                },
            )
        avg_price = Decimal(str(existing.avg_price))
        realized_pnl = compute_realized_pnl(avg_price, price, quantity)
        new_qty = held - quantity
        if new_qty == Decimal("0"):
            await holding_repo.delete(existing)
            holding = None
        else:
            existing.quantity = float(new_qty)
            holding = await holding_repo.update(existing)

    transaction = await tx_repo.create(
        portfolio_id=portfolio_id,
        asset_id=asset_id,
        transaction_type=tx_type,
        quantity=quantity,
        price=price,
        fees=fees,
        executed_at=executed_at,
    )

    # Update portfolio cash_balance: buy debits, sell credits; fees always deducted
    portfolio_result = await session.execute(
        select(Portfolio).where(Portfolio.id == portfolio_id)
    )
    portfolio = portfolio_result.scalar_one()
    cash_delta = (
        -(quantity * price + fees) if tx_type == "buy" else (quantity * price - fees)
    )
    portfolio.cash_balance = Decimal(str(portfolio.cash_balance)) + cash_delta

    await session.commit()
    return TransactionResult(transaction=transaction, holding=holding, realized_pnl=realized_pnl)
