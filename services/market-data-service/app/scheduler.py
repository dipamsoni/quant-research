"""APScheduler instance and job registration."""

from apscheduler.schedulers.asyncio import AsyncIOScheduler

scheduler = AsyncIOScheduler(timezone="UTC")


def register_jobs() -> None:
    from app.pipelines.news_pipeline import ingest_all_news
    from app.pipelines.ohlcv_pipeline import refresh_daily_candles

    scheduler.add_job(
        refresh_daily_candles,
        trigger="cron",
        hour=0,
        minute=5,
        id="daily_ohlcv_refresh",
        replace_existing=True,
        misfire_grace_time=3600,
    )

    scheduler.add_job(
        ingest_all_news,
        trigger="interval",
        minutes=10,
        id="news_ingest",
        replace_existing=True,
        misfire_grace_time=300,
    )
