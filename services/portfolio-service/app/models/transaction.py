import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, Numeric, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Transaction(Base):
    __tablename__ = "transactions"
    __table_args__ = (
        Index("idx_tx_portfolio", "portfolio_id"),
        Index("idx_tx_executed", "executed_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    portfolio_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("portfolios.id"), nullable=False
    )
    asset_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    transaction_type: Mapped[str] = mapped_column(String(10), nullable=False)  # 'buy' | 'sell'
    quantity: Mapped[float] = mapped_column(Numeric(28, 8), nullable=False)
    price: Mapped[float] = mapped_column(Numeric(20, 8), nullable=False)
    fees: Mapped[float] = mapped_column(Numeric(20, 8), nullable=False, default=0)
    executed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    portfolio: Mapped["Portfolio"] = relationship("Portfolio", back_populates="transactions")  # noqa: F821
