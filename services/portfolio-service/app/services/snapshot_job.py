"""Daily portfolio metrics snapshot job.

Runs at 15:30 IST (after NSE market close) and writes one row per portfolio
into portfolio_metrics.  Wired into main.py lifespan via get_scheduler().
"""
from __future__ import annotations

import structlog
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import select

from app.clients.market_data import MarketDataClient
from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.models.holding import Holding
from app.models.portfolio import Portfolio
from app.services.metrics import HoldingSnapshot, compute_and_store_metrics

logger = structlog.get_logger()


async def run_daily_snapshot() -> None:
    """Iterate every portfolio and compute + store today's metrics."""
    market_client = MarketDataClient()
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Portfolio))
        portfolios = list(result.scalars().all())

    for portfolio in portfolios:
        try:
            async with AsyncSessionLocal() as session:
                holdings_result = await session.execute(
                    select(Holding).where(Holding.portfolio_id == portfolio.id)
                )
                holdings = [
                    HoldingSnapshot(
                        symbol=h.symbol,
                        quantity=float(h.quantity),
                        avg_price=float(h.avg_price),
                    )
                    for h in holdings_result.scalars().all()
                ]
                await compute_and_store_metrics(
                    session=session,
                    portfolio_id=portfolio.id,
                    holdings=holdings,
                    market_client=market_client,
                )
        except Exception:
            logger.exception("snapshot_failed", portfolio_id=str(portfolio.id))


def get_scheduler() -> AsyncIOScheduler:
    """Return a configured scheduler; caller must call .start() / .shutdown()."""
    scheduler = AsyncIOScheduler(timezone="Asia/Kolkata")
    scheduler.add_job(
        run_daily_snapshot,
        trigger="cron",
        hour=15,
        minute=30,
        id="daily_portfolio_snapshot",
        replace_existing=True,
        misfire_grace_time=3600,
    )
    return scheduler


# Allow manual trigger for back-fill / testing
if __name__ == "__main__":
    import asyncio

    asyncio.run(run_daily_snapshot())
