"""Realtime ingestion pipeline: Binance WebSocket → TimescaleDB.

Only closed candles (k['x'] == True) are persisted.
Reconnects with exponential backoff on any connection error.
"""

from __future__ import annotations

import asyncio
import uuid
from datetime import datetime, timezone
from decimal import Decimal

import structlog
from binance import AsyncClient, BinanceSocketManager
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.pipelines.ohlcv_pipeline import _upsert_candles
from app.providers.base import OHLCVCandleSchema
from app.ws.connection_manager import PriceBus

logger = structlog.get_logger()

_BINANCE_INTERVAL_MAP: dict[str, str] = {
    "1m": "1m",
    "5m": "5m",
    "15m": "15m",
    "30m": "30m",
    "1h": "1h",
    "4h": "4h",
    "1d": "1d",
    "1w": "1w",
}

_RECONNECT_BASE_DELAY = 1.0
_RECONNECT_MAX_DELAY = 60.0


class RealtimePipeline:
    """Subscribes to Binance kline streams and persists closed candles."""

    def __init__(
        self,
        session_factory: async_sessionmaker,
        symbol_id_map: dict[str, uuid.UUID],
        api_key: str = "",
        api_secret: str = "",
        price_bus: PriceBus | None = None,
    ) -> None:
        self._session_factory = session_factory
        # symbol (uppercase, e.g. "BTCUSDT") → asset UUID in DB
        self._symbol_id_map = {s.upper(): uid for s, uid in symbol_id_map.items()}
        self._api_key = api_key
        self._api_secret = api_secret
        self._price_bus = price_bus
        self._task: asyncio.Task[None] | None = None
        self._running = False

    async def start(self, symbols: list[str], timeframe: str = "1m") -> None:
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(
            self._run_with_backoff(symbols, timeframe),
            name="realtime-pipeline",
        )
        logger.info("realtime_pipeline_started", symbols=symbols, timeframe=timeframe)

    async def stop(self) -> None:
        self._running = False
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("realtime_pipeline_stopped")

    async def _run_with_backoff(self, symbols: list[str], timeframe: str) -> None:
        delay = _RECONNECT_BASE_DELAY
        attempt = 0
        while self._running:
            try:
                await self._connect(symbols, timeframe)
                delay = _RECONNECT_BASE_DELAY
                attempt = 0
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                attempt += 1
                logger.warning(
                    "ws_reconnecting",
                    error=str(exc),
                    attempt=attempt,
                    next_delay_seconds=delay,
                )
                await asyncio.sleep(delay)
                delay = min(delay * 2, _RECONNECT_MAX_DELAY)

    async def _connect(self, symbols: list[str], timeframe: str) -> None:
        binance_interval = _BINANCE_INTERVAL_MAP.get(timeframe, timeframe)
        streams = [f"{s.lower()}@kline_{binance_interval}" for s in symbols]

        client = await AsyncClient.create(
            api_key=self._api_key or None,
            api_secret=self._api_secret or None,
        )
        try:
            bm = BinanceSocketManager(client)
            async with bm.multiplex_socket(streams) as socket:
                logger.info("ws_connected", stream_count=len(streams))
                while self._running:
                    msg: dict = await socket.recv()
                    if msg.get("e") == "error":
                        raise RuntimeError(f"Binance WS error: {msg}")
                    # multiplex wraps payload in {"stream": "...", "data": {...}}
                    data = msg.get("data", msg)
                    await self._handle_kline(data)
        finally:
            await client.close_connection()

    async def _handle_kline(self, msg: dict) -> None:
        k = msg.get("k")
        if not k:
            return

        symbol: str = k["s"].upper()

        # Publish latest price to WS clients on every kline (open or closed).
        # WS consumers want live price, not just closed-candle prices.
        if self._price_bus is not None:
            close_time_ms: int = k["T"]
            tick_ts = datetime.fromtimestamp(close_time_ms / 1000, tz=timezone.utc).isoformat()
            self._price_bus.publish(
                symbol,
                {"type": "tick", "symbol": symbol, "price": k["c"], "ts": tick_ts},
            )

        if not k.get("x"):
            return  # skip persistence for unclosed candles
        asset_id = self._symbol_id_map.get(symbol)
        if asset_id is None:
            logger.debug("ws_unknown_symbol", symbol=symbol)
            return

        open_time_ms: int = k["t"]
        dt = datetime.fromtimestamp(open_time_ms / 1000, tz=timezone.utc)

        base_vol = Decimal(str(k["v"]))
        quote_vol = Decimal(str(k["q"]))
        vwap = quote_vol / base_vol if base_vol > 0 else None

        # k["i"] is the interval string (e.g. "1m") — already canonical for our timeframes
        candle = OHLCVCandleSchema(
            time=dt,
            symbol=symbol,
            timeframe=k["i"],
            open=Decimal(str(k["o"])),
            high=Decimal(str(k["h"])),
            low=Decimal(str(k["l"])),
            close=Decimal(str(k["c"])),
            volume=base_vol,
            vwap=vwap,
            trade_count=int(k.get("n", 0)) or None,
            source="binance_ws",
        )

        async with self._session_factory() as db:
            inserted = await _upsert_candles(db, asset_id, [candle])
            if inserted:
                logger.debug(
                    "ws_candle_persisted",
                    symbol=symbol,
                    timeframe=candle.timeframe,
                    time=dt.isoformat(),
                )
