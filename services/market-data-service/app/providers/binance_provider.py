import asyncio
from datetime import datetime, timezone
from decimal import Decimal
from functools import partial

from binance.client import Client

from app.providers.base import MarketDataProvider, OHLCVCandleSchema

# Maps canonical timeframe → Binance kline interval constant.
# Binance natively uses the same strings as our canonical set for most timeframes.
_TIMEFRAME_MAP: dict[str, str] = {
    "1m": Client.KLINE_INTERVAL_1MINUTE,
    "5m": Client.KLINE_INTERVAL_5MINUTE,
    "15m": Client.KLINE_INTERVAL_15MINUTE,
    "30m": Client.KLINE_INTERVAL_30MINUTE,
    "1h": Client.KLINE_INTERVAL_1HOUR,
    "4h": Client.KLINE_INTERVAL_4HOUR,
    "1d": Client.KLINE_INTERVAL_1DAY,
    "1w": Client.KLINE_INTERVAL_1WEEK,
}

# Kline list indices (Binance API spec)
_IDX_OPEN_TIME = 0
_IDX_OPEN = 1
_IDX_HIGH = 2
_IDX_LOW = 3
_IDX_CLOSE = 4
_IDX_VOLUME = 5
_IDX_QUOTE_VOLUME = 7
_IDX_TRADE_COUNT = 8


class BinanceProvider(MarketDataProvider):
    def __init__(self, api_key: str = "", api_secret: str = "") -> None:
        # Public OHLCV endpoints don't require credentials; pass None when empty
        self._client = Client(
            api_key=api_key or None,
            api_secret=api_secret or None,
        )

    @property
    def source_name(self) -> str:
        return "binance"

    def supports_timeframe(self, timeframe: str) -> bool:
        return timeframe in _TIMEFRAME_MAP

    async def get_historical(
        self,
        symbol: str,
        timeframe: str,
        start: datetime,
        end: datetime,
    ) -> list[OHLCVCandleSchema]:
        if not self.supports_timeframe(timeframe):
            raise ValueError(f"Binance does not support timeframe '{timeframe}'")

        interval = _TIMEFRAME_MAP[timeframe]
        start_ms = int(start.timestamp() * 1000)
        end_ms = int(end.timestamp() * 1000)

        loop = asyncio.get_running_loop()
        klines: list[list] = await loop.run_in_executor(
            None,
            partial(
                self._client.get_klines,
                symbol=symbol,
                interval=interval,
                startTime=start_ms,
                endTime=end_ms,
            ),
        )
        return self._normalize(klines, symbol, timeframe)

    def _normalize(self, klines: list[list], symbol: str, timeframe: str) -> list[OHLCVCandleSchema]:
        candles: list[OHLCVCandleSchema] = []
        for kline in klines:
            dt = datetime.fromtimestamp(int(kline[_IDX_OPEN_TIME]) / 1000, tz=timezone.utc)
            base_vol = Decimal(str(kline[_IDX_VOLUME]))
            quote_vol = Decimal(str(kline[_IDX_QUOTE_VOLUME]))
            # VWAP approximation: total quote value traded / base volume
            vwap = quote_vol / base_vol if base_vol > 0 else None
            candles.append(
                OHLCVCandleSchema(
                    time=dt,
                    symbol=symbol,
                    timeframe=timeframe,
                    open=Decimal(str(kline[_IDX_OPEN])),
                    high=Decimal(str(kline[_IDX_HIGH])),
                    low=Decimal(str(kline[_IDX_LOW])),
                    close=Decimal(str(kline[_IDX_CLOSE])),
                    volume=base_vol,
                    vwap=vwap,
                    trade_count=int(kline[_IDX_TRADE_COUNT]),
                    source=self.source_name,
                )
            )
        return candles
