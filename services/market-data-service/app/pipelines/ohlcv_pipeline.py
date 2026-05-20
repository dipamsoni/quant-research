"""OHLCV ingestion pipeline: backfill, gap detection, upsert, daily refresh job."""

from __future__ import annotations

import asyncio
import uuid
from datetime import datetime, timedelta, timezone

import structlog
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.models.asset import Asset
from app.models.ohlcv import OHLCVCandle
from app.providers.base import MarketDataProvider, OHLCVCandleSchema, ProviderChain
from app.providers.binance_provider import BinanceProvider
from app.providers.yfinance_provider import YFinanceProvider

logger = structlog.get_logger()

# Limit concurrent yfinance calls to avoid IP-level throttling.
_YF_SEMAPHORE = asyncio.Semaphore(5)

# Expected interval in seconds per canonical timeframe.
# Gap threshold depends on asset type (crypto = 24/7, equity = market-hours).
_EXPECTED_SECONDS: dict[str, int] = {
    "1m": 60,
    "5m": 300,
    "15m": 900,
    "30m": 1800,
    "1h": 3600,
    "4h": 14400,
    "1d": 86400,
    "1w": 604800,
}

# For intraday equity timeframes, overnight + weekend gaps are normal.
# Use 36 h so we skip overnight gaps (~16 h) but still flag multi-day outages.
# Crypto uses the standard 3× multiplier (24/7 market, any gap is anomalous).
_EQUITY_INTRADAY_THRESHOLD_SECONDS = 36 * 3600
_INTRADAY_TIMEFRAMES = {"1m", "5m", "15m", "30m", "1h", "4h"}


def _gap_threshold(timeframe: str, asset_type: str) -> int:
    """Return gap threshold in seconds for this timeframe + asset type."""
    expected = _EXPECTED_SECONDS.get(timeframe)
    if expected is None:
        return 0
    if asset_type != "crypto" and timeframe in _INTRADAY_TIMEFRAMES:
        return _EQUITY_INTRADAY_THRESHOLD_SECONDS
    return expected * 3


def _detect_gaps(
    candles: list[OHLCVCandleSchema],
    timeframe: str,
    symbol: str,
    asset_type: str = "equity",
) -> int:
    """Log WARNING for gaps exceeding threshold. Returns gap count."""
    if len(candles) < 2:
        return 0
    threshold = _gap_threshold(timeframe, asset_type)
    if threshold == 0:
        return 0
    sorted_candles = sorted(candles, key=lambda c: c.time)
    gap_count = 0
    for prev, curr in zip(sorted_candles, sorted_candles[1:]):
        delta = (curr.time - prev.time).total_seconds()
        if delta > threshold:
            gap_count += 1
            logger.warning(
                "ohlcv_gap_detected",
                symbol=symbol,
                timeframe=timeframe,
                asset_type=asset_type,
                gap_start=prev.time.isoformat(),
                gap_end=curr.time.isoformat(),
                gap_seconds=int(delta),
                threshold_seconds=threshold,
            )
    return gap_count


async def _upsert_candles(
    db: AsyncSession,
    asset_id: uuid.UUID,
    candles: list[OHLCVCandleSchema],
) -> int:
    """Bulk upsert candles. ON CONFLICT DO UPDATE to handle split-adjusted restates."""
    if not candles:
        return 0
    rows = [
        {
            "time": c.time,
            "asset_id": asset_id,
            "timeframe": c.timeframe,
            "open": c.open,
            "high": c.high,
            "low": c.low,
            "close": c.close,
            "volume": c.volume,
            "vwap": c.vwap,
            "trade_count": c.trade_count,
            "source": c.source,
        }
        for c in candles
    ]
    stmt = pg_insert(OHLCVCandle).values(rows)
    stmt = stmt.on_conflict_do_update(
        index_elements=["time", "asset_id", "timeframe"],
        set_={
            "open": stmt.excluded.open,
            "high": stmt.excluded.high,
            "low": stmt.excluded.low,
            "close": stmt.excluded.close,
            "volume": stmt.excluded.volume,
            "vwap": stmt.excluded.vwap,
            "trade_count": stmt.excluded.trade_count,
            "source": stmt.excluded.source,
        },
    )
    result = await db.execute(stmt)
    await db.commit()
    return result.rowcount if result.rowcount >= 0 else len(rows)


async def get_asset_by_symbol(db: AsyncSession, symbol: str) -> Asset | None:
    result = await db.execute(select(Asset).where(Asset.symbol == symbol))
    return result.scalar_one_or_none()


async def _get_boundary_candle(
    db: AsyncSession,
    asset_id: uuid.UUID,
    timeframe: str,
    symbol: str,
    before: datetime,
) -> OHLCVCandleSchema | None:
    """Return the most recent stored candle before `before` for cross-run gap detection."""
    result = await db.execute(
        select(OHLCVCandle)
        .where(
            OHLCVCandle.asset_id == asset_id,
            OHLCVCandle.timeframe == timeframe,
            OHLCVCandle.time < before,
        )
        .order_by(OHLCVCandle.time.desc())
        .limit(1)
    )
    row = result.scalar_one_or_none()
    if row is None:
        return None
    return OHLCVCandleSchema(
        time=row.time,
        symbol=symbol,
        timeframe=timeframe,
        open=row.open,
        high=row.high,
        low=row.low,
        close=row.close,
        volume=row.volume,
        vwap=row.vwap,
        trade_count=row.trade_count,
        source=row.source,
    )


async def backfill(
    db: AsyncSession,
    asset: Asset,
    timeframe: str,
    start: datetime,
    end: datetime,
    provider: MarketDataProvider,
) -> int:
    """Fetch historical candles from provider, detect gaps (including cross-run), upsert."""
    log = logger.bind(symbol=asset.symbol, timeframe=timeframe, provider=provider.source_name)
    log.info("backfill_start", start=start.isoformat(), end=end.isoformat())

    try:
        candles = await provider.get_historical(asset.symbol, timeframe, start, end)
    except Exception as exc:
        log.error("backfill_fetch_failed", error=str(exc))
        return 0

    log.info("backfill_fetched", count=len(candles))

    if not candles:
        log.warning("backfill_empty", start=start.isoformat(), end=end.isoformat())
        return 0

    # Prepend the last stored candle to detect cross-run gaps.
    boundary = await _get_boundary_candle(db, asset.id, timeframe, asset.symbol, start)
    candles_for_gap_check = ([boundary] + list(candles)) if boundary else list(candles)

    asset_type: str = getattr(asset, "asset_type", "equity") or "equity"
    _detect_gaps(candles_for_gap_check, timeframe, asset.symbol, asset_type)

    inserted = await _upsert_candles(db, asset.id, candles)
    log.info("backfill_complete", fetched=len(candles), inserted=inserted)
    return inserted


async def refresh_daily_candles() -> None:
    """APScheduler job: pull yesterday's 1d candle for every active asset."""
    now_utc = datetime.now(tz=timezone.utc)
    end = now_utc.replace(hour=0, minute=0, second=0, microsecond=0)
    start = end - timedelta(days=1)

    yf_provider = YFinanceProvider()
    binance_provider = BinanceProvider(
        api_key=settings.BINANCE_API_KEY,
        api_secret=settings.BINANCE_API_SECRET,
    )
    # Crypto: Binance primary, yfinance fallback.
    # Equity: yfinance primary (no free alternative; chain logs if it fails).
    crypto_chain = ProviderChain([binance_provider, yf_provider])
    equity_chain = ProviderChain([yf_provider])

    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Asset).where(Asset.is_active.is_(True)))
        assets: list[Asset] = list(result.scalars().all())

    logger.info("daily_refresh_start", asset_count=len(assets), date=start.date().isoformat())

    async def _refresh_one(asset: Asset) -> None:
        chain = crypto_chain if asset.asset_type == "crypto" else equity_chain
        if not chain.supports_timeframe("1d"):
            return
        # Throttle yfinance-backed calls to avoid IP throttling.
        context = _YF_SEMAPHORE if asset.asset_type != "crypto" else asyncio.nullcontext()
        async with context:
            try:
                async with AsyncSessionLocal() as db:
                    inserted = await backfill(db, asset, "1d", start, end, chain)
                logger.info("daily_refresh_ok", symbol=asset.symbol, inserted=inserted)
            except Exception as exc:
                logger.error("daily_refresh_failed", symbol=asset.symbol, error=str(exc))

    await asyncio.gather(*[_refresh_one(asset) for asset in assets])
