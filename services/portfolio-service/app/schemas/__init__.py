from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, ConfigDict, field_validator

T = TypeVar("T")


class APISuccess(BaseModel, Generic[T]):
    success: bool = True
    data: T
    meta: dict[str, Any] | None = None


# ── Requests ──────────────────────────────────────────────────────────────────


class PortfolioCreate(BaseModel):
    name: str
    base_currency: str = "INR"
    risk_profile: str | None = None
    initial_cash: Decimal = Decimal("0")


class TransactionCreate(BaseModel):
    asset_id: uuid.UUID
    symbol: str
    transaction_type: str
    quantity: Decimal
    price: Decimal
    fees: Decimal = Decimal("0")
    executed_at: datetime | None = None

    @field_validator("transaction_type")
    @classmethod
    def _validate_tx_type(cls, v: str) -> str:
        if v.lower() not in ("buy", "sell"):
            raise ValueError("transaction_type must be 'buy' or 'sell'")
        return v


# ── Responses ─────────────────────────────────────────────────────────────────


class PortfolioResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    name: str
    base_currency: str
    risk_profile: str | None
    cash_balance: Decimal
    created_at: datetime


class HoldingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    asset_id: uuid.UUID
    symbol: str
    quantity: float
    avg_price: float
    market_value: float | None


class MetricsSnapshotResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    date: date
    total_value: float
    daily_return: float | None
    sharpe_ratio: float | None
    max_drawdown: float | None
    volatility: float | None
    beta: float | None
    alpha: float | None
    cost_basis: float | None
    unrealized_pnl: float | None
    realized_pnl: float | None


class PortfolioDetailResponse(PortfolioResponse):
    holdings: list[HoldingResponse]
    latest_metrics: MetricsSnapshotResponse | None


class TransactionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    portfolio_id: uuid.UUID
    asset_id: uuid.UUID
    transaction_type: str
    quantity: float
    price: float
    fees: float
    executed_at: datetime
    realized_pnl: Decimal | None = None


class AllocationItem(BaseModel):
    asset_id: uuid.UUID
    value: float
    pct: float


class AllocationResponse(BaseModel):
    total_value: float
    allocations: list[AllocationItem]
