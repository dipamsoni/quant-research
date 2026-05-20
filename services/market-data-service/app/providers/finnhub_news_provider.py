"""Finnhub company-news provider.

Free tier: 60 req/min. Callers must enforce rate limits externally.
API docs: https://finnhub.io/docs/api/company-news
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone

import httpx
import structlog
from pydantic import BaseModel

logger = structlog.get_logger()

_BASE_URL = "https://finnhub.io/api/v1"
_MAX_RETRIES = 3
_RETRY_BASE_DELAY = 2.0


class NewsArticleSchema(BaseModel):
    """Normalized news DTO returned by all news provider adapters."""

    title: str
    content: str | None
    source: str
    url: str
    published_at: datetime
    symbols: list[str]

    model_config = {"frozen": True}


class FinnhubNewsProvider:
    def __init__(self, api_key: str) -> None:
        self._api_key = api_key
        self._client = httpx.AsyncClient(
            base_url=_BASE_URL,
            timeout=10.0,
            headers={"X-Finnhub-Token": api_key},
        )

    async def aclose(self) -> None:
        await self._client.aclose()

    async def get_company_news(
        self,
        symbol: str,
        from_dt: datetime,
        to_dt: datetime,
    ) -> list[NewsArticleSchema]:
        """Fetch company news for symbol. Retries up to 3× with Retry-After awareness."""
        params = {
            "symbol": symbol,
            "from": from_dt.strftime("%Y-%m-%d"),
            "to": to_dt.strftime("%Y-%m-%d"),
        }
        delay = _RETRY_BASE_DELAY
        for attempt in range(1, _MAX_RETRIES + 1):
            resp = await self._client.get("/company-news", params=params)
            if resp.status_code == 429:
                retry_after = float(resp.headers.get("Retry-After", delay))
                logger.warning(
                    "finnhub_rate_limited",
                    symbol=symbol,
                    attempt=attempt,
                    retry_after_seconds=retry_after,
                )
                if attempt < _MAX_RETRIES:
                    await asyncio.sleep(retry_after)
                    delay = min(delay * 2, 60.0)
                    continue
            resp.raise_for_status()
            items: list[dict] = resp.json()
            return [self._normalize(item, symbol) for item in items if item.get("url")]
        resp.raise_for_status()
        return []

    @staticmethod
    def _normalize(item: dict, symbol: str) -> NewsArticleSchema:
        ts = item.get("datetime", 0)
        published_at = datetime.fromtimestamp(ts, tz=timezone.utc)
        return NewsArticleSchema(
            title=item.get("headline") or item.get("summary") or "",
            content=item.get("summary"),
            source=item.get("source") or "finnhub",
            url=item["url"],
            published_at=published_at,
            symbols=[symbol],
        )
