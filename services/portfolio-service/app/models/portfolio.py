import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Portfolio(Base):
    __tablename__ = "portfolios"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    base_currency: Mapped[str] = mapped_column(String(10), nullable=False, default="INR")
    risk_profile: Mapped[str | None] = mapped_column(Text, nullable=True)
    cash_balance: Mapped[Decimal] = mapped_column(
        Numeric(28, 8), nullable=False, server_default="0"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    holdings: Mapped[list["Holding"]] = relationship(  # noqa: F821
        "Holding", back_populates="portfolio", cascade="all, delete-orphan"
    )
    transactions: Mapped[list["Transaction"]] = relationship(  # noqa: F821
        "Transaction", back_populates="portfolio", cascade="all, delete-orphan"
    )
    metrics: Mapped[list["PortfolioMetrics"]] = relationship(  # noqa: F821
        "PortfolioMetrics", back_populates="portfolio", cascade="all, delete-orphan"
    )
