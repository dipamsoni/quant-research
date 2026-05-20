#!/usr/bin/env python3
"""Initial 2-year daily OHLCV backfill for all active assets.

Run once after seeding assets:
    uv run python scripts/backfill_initial.py

Re-running is safe — upsert deduplicates existing candles.
"""

from __future__ import annotations

import asyncio
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

_SERVICE_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_SERVICE_ROOT))

import structlog
from sqlalchemy import select

from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.core.logging import configure_logging
from app.models.asset import Asset
from app.pipelines.ohlcv_pipeline import backfill
from app.providers.base import ProviderChain
from app.providers.binance_provider import BinanceProvider
from app.providers.yfinance_provider import YFinanceProvider

configure_logging()
logger = structlog.get_logger()

BACKFILL_DAYS = 730  # 2 years
# Throttle concurrent yfinance requests to avoid IP-level rate limiting.
_EQUITY_SEM = asyncio.Semaphore(5)
_CRYPTO_SEM = asyncio.Semaphore(10)


async def _backfill_one(
    asset: Asset,
    start: datetime,
    end: datetime,
    equity_chain: ProviderChain,
    crypto_chain: ProviderChain,
) -> None:
    chain = crypto_chain if asset.asset_type == "crypto" else equity_chain
    sem = _CRYPTO_SEM if asset.asset_type == "crypto" else _EQUITY_SEM
    async with sem:
        try:
            async with AsyncSessionLocal() as db:
                inserted = await backfill(db, asset, "1d", start, end, chain)
            logger.info("backfill_asset_ok", symbol=asset.symbol, inserted=inserted)
        except Exception as exc:
            logger.error("backfill_asset_failed", symbol=asset.symbol, error=str(exc))


async def main() -> None:
    end = datetime.now(tz=timezone.utc)
    start = end - timedelta(days=BACKFILL_DAYS)

    yf = YFinanceProvider()
    binance = BinanceProvider(
        api_key=settings.BINANCE_API_KEY,
        api_secret=settings.BINANCE_API_SECRET,
    )
    equity_chain = ProviderChain([yf])
    crypto_chain = ProviderChain([binance, yf])

    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Asset).where(Asset.is_active.is_(True)))
        assets: list[Asset] = list(result.scalars().all())

    logger.info(
        "initial_backfill_start",
        asset_count=len(assets),
        start=start.date().isoformat(),
        end=end.date().isoformat(),
        days=BACKFILL_DAYS,
    )

    await asyncio.gather(
        *[_backfill_one(a, start, end, equity_chain, crypto_chain) for a in assets]
    )

    logger.info("initial_backfill_done", asset_count=len(assets))


if __name__ == "__main__":
    asyncio.run(main())
