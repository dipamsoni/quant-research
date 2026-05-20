"""News ingestion pipeline: fetch, dedup by URL, upsert to news_articles.

Backfill strategy:
- First run per symbol (no Redis key): pull last 24 h.
- Subsequent runs: pull from last_ingested timestamp.
Redis key: news:last_ingested:{symbol}  value: ISO-8601 UTC string

Rate limit: Finnhub free = 60 req/min.
- We sleep 1 s between per-symbol requests (~55 req/min headroom).
- If active asset count > _MAX_SYMBOLS_PER_RUN, we rotate via a Redis cursor
  so every symbol gets coverage across consecutive runs.
- On HTTP 429, pause the entire batch for 60 s before continuing.

Fallback: if NEWSAPI_KEY is set, use NewsAPI when Finnhub fails.
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone

import httpx
import structlog
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.core.redis import get_redis
from app.models.asset import Asset
from app.models.news import NewsArticle
from app.providers.finnhub_news_provider import FinnhubNewsProvider, NewsArticleSchema
from app.providers.newsapi_provider import NewsAPIProvider

logger = structlog.get_logger()

_REDIS_KEY = "news:last_ingested:{symbol}"
_REDIS_CURSOR_KEY = "news:ingest_cursor"
_MAX_SYMBOLS_PER_RUN = 55  # stay under 60 req/min with 1 s sleep
_BACKFILL_HOURS = 24
_RATE_LIMIT_PAUSE = 60.0  # seconds to pause batch on HTTP 429


def _last_key(symbol: str) -> str:
    return _REDIS_KEY.format(symbol=symbol)


async def _get_last_ingested(symbol: str) -> datetime | None:
    redis = get_redis()
    val = await redis.get(_last_key(symbol))
    if val is None:
        return None
    return datetime.fromisoformat(val)


async def _set_last_ingested(symbol: str, dt: datetime) -> None:
    redis = get_redis()
    await redis.set(_last_key(symbol), dt.isoformat())


async def _upsert_articles(articles: list[NewsArticleSchema]) -> int:
    """Bulk upsert; skips duplicates via ON CONFLICT (url) DO NOTHING. Returns insert count."""
    if not articles:
        return 0
    rows = [
        {
            "title": a.title,
            "content": a.content,
            "source": a.source,
            "url": a.url,
            "published_at": a.published_at,
            "symbols": a.symbols,
        }
        for a in articles
    ]
    async with AsyncSessionLocal() as db:
        stmt = pg_insert(NewsArticle).values(rows).on_conflict_do_nothing(index_elements=["url"])
        result = await db.execute(stmt)
        await db.commit()
    return result.rowcount if result.rowcount >= 0 else len(rows)


async def ingest_news_for_symbol(
    symbol: str,
    primary: FinnhubNewsProvider,
    fallback: NewsAPIProvider | None = None,
) -> tuple[int, bool]:
    """Fetch and upsert news for one symbol.

    Returns (inserted_count, rate_limited).
    `rate_limited` is True when the primary provider returned HTTP 429 after retries.
    """
    now = datetime.now(tz=timezone.utc)
    last = await _get_last_ingested(symbol)
    from_dt = last if last is not None else (now - timedelta(hours=_BACKFILL_HOURS))

    log = logger.bind(symbol=symbol, from_dt=from_dt.isoformat(), to_dt=now.isoformat())
    log.info("news_ingest_start", backfill=(last is None))

    articles: list[NewsArticleSchema] = []
    rate_limited = False

    try:
        articles = await primary.get_company_news(symbol, from_dt, now)
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 429:
            rate_limited = True
            log.warning("news_fetch_rate_limited", provider="finnhub")
        else:
            log.error("news_fetch_failed", provider="finnhub", error=str(exc))
    except Exception as exc:
        log.error("news_fetch_failed", provider="finnhub", error=str(exc))

    # Fallback to NewsAPI when Finnhub fails (and fallback provider is configured).
    if not articles and not rate_limited and fallback is not None:
        try:
            articles = await fallback.get_company_news(symbol, from_dt, now)
            if articles:
                log.info("news_fetch_fallback_ok", provider="newsapi", count=len(articles))
        except Exception as exc:
            log.error("news_fetch_failed", provider="newsapi", error=str(exc))

    if not articles:
        return 0, rate_limited

    inserted = await _upsert_articles(articles)
    await _set_last_ingested(symbol, now)
    log.info("news_ingest_done", fetched=len(articles), inserted=inserted)
    return inserted, rate_limited


async def ingest_all_news() -> None:
    """APScheduler job: ingest news for all active assets (rate-limited)."""
    if not settings.FINNHUB_API_KEY:
        logger.warning("news_ingest_skipped", reason="FINNHUB_API_KEY not set")
        return

    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Asset.symbol).where(Asset.is_active.is_(True)))
        all_symbols: list[str] = list(result.scalars().all())

    if not all_symbols:
        logger.info("news_ingest_skipped", reason="no active assets")
        return

    # Rotate through symbols across runs so every symbol gets coverage.
    redis = get_redis()
    cursor_val = await redis.get(_REDIS_CURSOR_KEY)
    cursor = int(cursor_val) if cursor_val else 0
    cursor = cursor % len(all_symbols)

    rotated = all_symbols[cursor:] + all_symbols[:cursor]
    batch = rotated[:_MAX_SYMBOLS_PER_RUN]
    next_cursor = (cursor + len(batch)) % len(all_symbols)
    await redis.set(_REDIS_CURSOR_KEY, str(next_cursor))

    if len(all_symbols) > _MAX_SYMBOLS_PER_RUN:
        logger.warning(
            "news_ingest_batch",
            total=len(all_symbols),
            batch=len(batch),
            cursor=cursor,
        )

    primary = FinnhubNewsProvider(api_key=settings.FINNHUB_API_KEY)
    fallback: NewsAPIProvider | None = (
        NewsAPIProvider(api_key=settings.NEWSAPI_KEY) if settings.NEWSAPI_KEY else None
    )

    total_inserted = 0
    try:
        for i, symbol in enumerate(batch):
            inserted, rate_limited = await ingest_news_for_symbol(symbol, primary, fallback)
            total_inserted += inserted

            if rate_limited:
                logger.warning(
                    "news_ingest_rate_limit_pause",
                    symbol=symbol,
                    pause_seconds=_RATE_LIMIT_PAUSE,
                )
                await asyncio.sleep(_RATE_LIMIT_PAUSE)
            elif i < len(batch) - 1:
                await asyncio.sleep(1.0)
    finally:
        await primary.aclose()
        if fallback is not None:
            await fallback.aclose()

    logger.info("news_ingest_run_complete", symbols=len(batch), inserted=total_inserted)
