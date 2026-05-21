import uuid
from datetime import date, datetime

from sqlalchemy import Date, ForeignKey, Numeric, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class PortfolioMetrics(Base):
    __tablename__ = "portfolio_metrics"
    __table_args__ = (
        UniqueConstraint("portfolio_id", "date", name="uq_portfolio_metrics_portfolio_date"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    portfolio_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("portfolios.id"), nullable=False, index=True
    )
    date: Mapped[date] = mapped_column(Date, nullable=False)
    total_value: Mapped[float] = mapped_column(Numeric(28, 8), nullable=False)
    daily_return: Mapped[float | None] = mapped_column(Numeric(10, 8), nullable=True)
    sharpe_ratio: Mapped[float | None] = mapped_column(Numeric(10, 4), nullable=True)
    max_drawdown: Mapped[float | None] = mapped_column(Numeric(10, 8), nullable=True)
    volatility: Mapped[float | None] = mapped_column(Numeric(10, 8), nullable=True)
    beta: Mapped[float | None] = mapped_column(Numeric(10, 6), nullable=True)
    alpha: Mapped[float | None] = mapped_column(Numeric(10, 8), nullable=True)
    cost_basis: Mapped[float | None] = mapped_column(Numeric(28, 8), nullable=True)
    unrealized_pnl: Mapped[float | None] = mapped_column(Numeric(28, 8), nullable=True)
    realized_pnl: Mapped[float | None] = mapped_column(Numeric(28, 8), nullable=True)

    portfolio: Mapped["Portfolio"] = relationship("Portfolio", back_populates="metrics")  # noqa: F821
