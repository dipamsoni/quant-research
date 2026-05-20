import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import TIMESTAMP, ForeignKey, Integer, Numeric, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class OHLCVCandle(Base):
    __tablename__ = "ohlcv_candles"

    # Composite PK — TimescaleDB requires the partition key (time) in the PK
    time: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), primary_key=True)
    asset_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("assets.id", ondelete="CASCADE"),
        primary_key=True,
    )
    timeframe: Mapped[str] = mapped_column(Text, primary_key=True)

    open: Mapped[Decimal] = mapped_column(Numeric(20, 8), nullable=False)
    high: Mapped[Decimal] = mapped_column(Numeric(20, 8), nullable=False)
    low: Mapped[Decimal] = mapped_column(Numeric(20, 8), nullable=False)
    close: Mapped[Decimal] = mapped_column(Numeric(20, 8), nullable=False)
    volume: Mapped[Decimal] = mapped_column(Numeric(28, 8), nullable=False)
    vwap: Mapped[Decimal | None] = mapped_column(Numeric(20, 8), nullable=True)
    trade_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    source: Mapped[str] = mapped_column(Text, nullable=False)
