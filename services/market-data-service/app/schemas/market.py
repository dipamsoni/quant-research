from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, ConfigDict

T = TypeVar("T")


class Pagination(BaseModel):
    next_cursor: str | None = None
    has_more: bool


class APISuccess(BaseModel, Generic[T]):
    success: bool = True
    data: T
    pagination: Pagination | None = None
    meta: dict[str, Any] | None = None


class AssetResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    symbol: str
    name: str
    asset_type: str
    exchange: str
    currency: str
    sector: str | None = None
    industry: str | None = None


class AssetDetailResponse(AssetResponse):
    price: Decimal | None = None
    as_of: datetime | None = None


class IndicatorValues(BaseModel):
    sma_20: float | None = None
    ema_50: float | None = None
    rsi_14: float | None = None
    macd_macd: float | None = None
    macd_signal: float | None = None
    macd_histogram: float | None = None
    bb_upper: float | None = None
    bb_middle: float | None = None
    bb_lower: float | None = None


class CandleResponse(BaseModel):
    time: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float
    indicators: IndicatorValues | None = None


class PriceResponse(BaseModel):
    symbol: str
    price: Decimal
    as_of: datetime


class NewsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    source: str
    url: str
    published_at: datetime
    symbols: list[str] | None = None
    sentiment_score: Decimal | None = None


class WatchlistItemResponse(BaseModel):
    id: uuid.UUID
    symbol: str
    name: str
    asset_type: str
    exchange: str
    added_at: datetime


class WatchlistAddRequest(BaseModel):
    symbol: str
