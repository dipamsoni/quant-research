import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Numeric, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Holding(Base):
    __tablename__ = "holdings"
    __table_args__ = (UniqueConstraint("portfolio_id", "asset_id", name="uq_holdings_portfolio_asset"),)

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    portfolio_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("portfolios.id"), nullable=False, index=True
    )
    asset_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    symbol: Mapped[str] = mapped_column(String(50), nullable=False, server_default="UNKNOWN")
    quantity: Mapped[float] = mapped_column(Numeric(28, 8), nullable=False)
    avg_price: Mapped[float] = mapped_column(Numeric(20, 8), nullable=False)
    market_value: Mapped[float | None] = mapped_column(Numeric(28, 8), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    portfolio: Mapped["Portfolio"] = relationship("Portfolio", back_populates="holdings")  # noqa: F821
