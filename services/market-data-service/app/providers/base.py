from abc import ABC, abstractmethod
from datetime import datetime
from decimal import Decimal

import structlog
from pydantic import BaseModel

logger = structlog.get_logger()


class OHLCVCandleSchema(BaseModel):
    """Normalized OHLCV DTO returned by all provider adapters."""

    time: datetime
    symbol: str
    timeframe: str
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: Decimal
    vwap: Decimal | None = None
    trade_count: int | None = None
    source: str

    model_config = {"frozen": True}


class MarketDataProvider(ABC):
    @property
    @abstractmethod
    def source_name(self) -> str: ...

    @abstractmethod
    def supports_timeframe(self, timeframe: str) -> bool: ...

    @abstractmethod
    async def get_historical(
        self,
        symbol: str,
        timeframe: str,
        start: datetime,
        end: datetime,
    ) -> list[OHLCVCandleSchema]: ...


class ProviderChain(MarketDataProvider):
    """Try providers in priority order; fall back to next on any exception."""

    def __init__(self, providers: list[MarketDataProvider]) -> None:
        if not providers:
            raise ValueError("ProviderChain requires at least one provider")
        self._providers = providers

    @property
    def source_name(self) -> str:
        return "+".join(p.source_name for p in self._providers)

    def supports_timeframe(self, timeframe: str) -> bool:
        return any(p.supports_timeframe(timeframe) for p in self._providers)

    async def get_historical(
        self,
        symbol: str,
        timeframe: str,
        start: datetime,
        end: datetime,
    ) -> list[OHLCVCandleSchema]:
        last_exc: Exception | None = None
        for provider in self._providers:
            if not provider.supports_timeframe(timeframe):
                continue
            try:
                result = await provider.get_historical(symbol, timeframe, start, end)
                if result:
                    return result
                # empty result → try next provider
                logger.warning(
                    "provider_empty_result",
                    provider=provider.source_name,
                    symbol=symbol,
                    timeframe=timeframe,
                )
            except Exception as exc:
                logger.warning(
                    "provider_fallback",
                    provider=provider.source_name,
                    symbol=symbol,
                    timeframe=timeframe,
                    error=str(exc),
                )
                last_exc = exc
        if last_exc is not None:
            raise last_exc
        return []
