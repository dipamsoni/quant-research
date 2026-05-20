import asyncio
import time
from datetime import datetime, timezone
from decimal import Decimal
from functools import partial

import pandas as pd
from alpha_vantage.timeseries import TimeSeries

from app.providers.base import MarketDataProvider, OHLCVCandleSchema

# Maps canonical timeframe → AlphaVantage interval string for intraday endpoint
_INTRADAY_MAP: dict[str, str] = {
    "1m": "1min",
    "5m": "5min",
    "15m": "15min",
    "30m": "30min",
    "1h": "60min",
}

_DAILY_TIMEFRAMES = {"1d", "1w"}

# Free tier: 5 req/min → enforce minimum 12 s between calls across all instances.
_AV_MIN_INTERVAL = 12.0
_av_lock = asyncio.Lock()
_av_last_call_at: float = 0.0


async def _av_rate_limit() -> None:
    global _av_last_call_at
    async with _av_lock:
        now = time.monotonic()
        wait = _AV_MIN_INTERVAL - (now - _av_last_call_at)
        if wait > 0:
            await asyncio.sleep(wait)
        _av_last_call_at = time.monotonic()


class AlphaVantageProvider(MarketDataProvider):
    def __init__(self, api_key: str) -> None:
        if not api_key:
            raise ValueError("AlphaVantageProvider requires an API key")
        self._api_key = api_key

    @property
    def source_name(self) -> str:
        return "alphavantage"

    def supports_timeframe(self, timeframe: str) -> bool:
        return timeframe in _INTRADAY_MAP or timeframe in _DAILY_TIMEFRAMES

    async def get_historical(
        self,
        symbol: str,
        timeframe: str,
        start: datetime,
        end: datetime,
    ) -> list[OHLCVCandleSchema]:
        if not self.supports_timeframe(timeframe):
            raise ValueError(f"AlphaVantage does not support timeframe '{timeframe}'")

        await _av_rate_limit()
        ts = TimeSeries(key=self._api_key, output_format="pandas")
        loop = asyncio.get_running_loop()

        if timeframe in _INTRADAY_MAP:
            interval = _INTRADAY_MAP[timeframe]
            data, _ = await loop.run_in_executor(
                None,
                partial(ts.get_intraday, symbol=symbol, interval=interval, outputsize="full"),
            )
        elif timeframe == "1d":
            data, _ = await loop.run_in_executor(
                None,
                partial(ts.get_daily, symbol=symbol, outputsize="full"),
            )
        else:  # "1w"
            data, _ = await loop.run_in_executor(
                None,
                partial(ts.get_weekly, symbol=symbol),
            )

        return self._normalize(data, symbol, timeframe, start, end)

    def _normalize(
        self,
        df: pd.DataFrame,
        symbol: str,
        timeframe: str,
        start: datetime,
        end: datetime,
    ) -> list[OHLCVCandleSchema]:
        if df.empty:
            return []

        df = df.sort_index(ascending=True)

        # alpha_vantage returns tz-naive index; compare without tz
        start_naive = start.replace(tzinfo=None)
        end_naive = end.replace(tzinfo=None)
        naive_idx = df.index.tz_convert(None) if df.index.tz is not None else df.index
        mask = (naive_idx >= start_naive) & (naive_idx <= end_naive)
        df = df[mask]

        candles: list[OHLCVCandleSchema] = []
        for ts, row in df.iterrows():
            dt = ts.to_pydatetime()
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            candles.append(
                OHLCVCandleSchema(
                    time=dt,
                    symbol=symbol,
                    timeframe=timeframe,
                    open=Decimal(str(row["1. open"])),
                    high=Decimal(str(row["2. high"])),
                    low=Decimal(str(row["3. low"])),
                    close=Decimal(str(row["4. close"])),
                    volume=Decimal(str(row["5. volume"])),
                    source=self.source_name,
                )
            )
        return candles
