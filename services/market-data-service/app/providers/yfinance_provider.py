import asyncio
from datetime import datetime, timezone
from decimal import Decimal
from functools import partial

import pandas as pd
import yfinance as yf

from app.providers.base import MarketDataProvider, OHLCVCandleSchema

# Maps canonical timeframe → yfinance interval string
_TIMEFRAME_MAP: dict[str, str] = {
    "1m": "1m",
    "5m": "5m",
    "15m": "15m",
    "30m": "30m",
    "1h": "1h",
    "1d": "1d",
    "1w": "1wk",
}


class YFinanceProvider(MarketDataProvider):
    @property
    def source_name(self) -> str:
        return "yfinance"

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
            raise ValueError(f"yfinance does not support timeframe '{timeframe}'")

        interval = _TIMEFRAME_MAP[timeframe]
        loop = asyncio.get_running_loop()
        df: pd.DataFrame = await loop.run_in_executor(
            None,
            partial(
                yf.download,
                tickers=symbol,
                start=start,
                end=end,
                interval=interval,
                auto_adjust=True,
                progress=False,
                multi_level_index=False,
            ),
        )
        return self._normalize(df, symbol, timeframe)

    def _normalize(self, df: pd.DataFrame, symbol: str, timeframe: str) -> list[OHLCVCandleSchema]:
        if df.empty:
            return []

        # Flatten MultiIndex columns produced by some yfinance versions
        if isinstance(df.columns, pd.MultiIndex):
            df = df.copy()
            df.columns = df.columns.get_level_values(0)

        df = df.copy()
        df.columns = [str(c).lower() for c in df.columns]

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
                    open=Decimal(str(row["open"])),
                    high=Decimal(str(row["high"])),
                    low=Decimal(str(row["low"])),
                    close=Decimal(str(row["close"])),
                    volume=Decimal(str(row["volume"])),
                    source=self.source_name,
                )
            )
        return candles
