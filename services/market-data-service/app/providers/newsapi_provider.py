"""NewsAPI.org news provider — used as fallback when Finnhub is unavailable.

Free tier: 100 req/day. Only use as fallback.
API docs: https://newsapi.org/docs/endpoints/everything
"""

from __future__ import annotations

from datetime import datetime, timezone

import httpx

from app.providers.finnhub_news_provider import NewsArticleSchema

_BASE_URL = "https://newsapi.org/v2"


class NewsAPIProvider:
    def __init__(self, api_key: str) -> None:
        if not api_key:
            raise ValueError("NewsAPIProvider requires an API key")
        self._client = httpx.AsyncClient(
            base_url=_BASE_URL,
            timeout=10.0,
            headers={"X-Api-Key": api_key},
        )

    async def aclose(self) -> None:
        await self._client.aclose()

    async def get_company_news(
        self,
        symbol: str,
        from_dt: datetime,
        to_dt: datetime,
    ) -> list[NewsArticleSchema]:
        """Fetch news for symbol from NewsAPI /everything endpoint."""
        resp = await self._client.get(
            "/everything",
            params={
                "q": symbol,
                "from": from_dt.strftime("%Y-%m-%dT%H:%M:%S"),
                "to": to_dt.strftime("%Y-%m-%dT%H:%M:%S"),
                "language": "en",
                "sortBy": "publishedAt",
                "pageSize": 100,
            },
        )
        resp.raise_for_status()
        payload = resp.json()
        articles = payload.get("articles", [])
        return [self._normalize(a, symbol) for a in articles if a.get("url")]

    @staticmethod
    def _normalize(item: dict, symbol: str) -> NewsArticleSchema:
        raw_ts: str = item.get("publishedAt") or ""
        try:
            published_at = datetime.fromisoformat(raw_ts.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            published_at = datetime.now(tz=timezone.utc)
        source_name: str = (item.get("source") or {}).get("name") or "newsapi"
        return NewsArticleSchema(
            title=item.get("title") or "",
            content=item.get("description") or item.get("content"),
            source=source_name,
            url=item["url"],
            published_at=published_at,
            symbols=[symbol],
        )
