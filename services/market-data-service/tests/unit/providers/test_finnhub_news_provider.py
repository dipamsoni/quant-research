from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.providers.finnhub_news_provider import FinnhubNewsProvider, NewsArticleSchema


def _make_item(
    url: str = "https://example.com/news/1",
    headline: str = "RELIANCE Hits 52-Week High",
    summary: str = "Reliance Industries stock hit a record.",
    source: str = "Reuters",
    ts: int = 1_700_000_000,
) -> dict:
    return {
        "url": url,
        "headline": headline,
        "summary": summary,
        "source": source,
        "datetime": ts,
        "category": "company",
        "id": 123,
        "image": "",
        "related": "RELIANCE",
    }


@pytest.fixture
def provider() -> FinnhubNewsProvider:
    return FinnhubNewsProvider(api_key="test-key")


class TestFinnhubNewsProvider:
    def test_normalize_maps_fields(self, provider: FinnhubNewsProvider) -> None:
        item = _make_item()
        article = provider._normalize(item, "RELIANCE")

        assert isinstance(article, NewsArticleSchema)
        assert article.title == "RELIANCE Hits 52-Week High"
        assert article.content == "Reliance Industries stock hit a record."
        assert article.source == "Reuters"
        assert article.url == "https://example.com/news/1"
        assert article.symbols == ["RELIANCE"]
        assert article.published_at == datetime.fromtimestamp(1_700_000_000, tz=timezone.utc)

    def test_normalize_tz_aware(self, provider: FinnhubNewsProvider) -> None:
        article = provider._normalize(_make_item(), "TCS")
        assert article.published_at.tzinfo is not None

    def test_normalize_uses_summary_as_title_when_no_headline(
        self, provider: FinnhubNewsProvider
    ) -> None:
        item = _make_item(headline="")
        article = provider._normalize(item, "INFY")
        assert article.title == "Reliance Industries stock hit a record."

    async def test_get_company_news_parses_response(self, provider: FinnhubNewsProvider) -> None:
        items = [_make_item(), _make_item(url="https://example.com/2", headline="Another story")]
        mock_resp = MagicMock()
        mock_resp.json.return_value = items
        mock_resp.raise_for_status = MagicMock()

        with patch.object(provider._client, "get", new=AsyncMock(return_value=mock_resp)):
            articles = await provider.get_company_news(
                "RELIANCE",
                datetime(2024, 1, 1, tzinfo=timezone.utc),
                datetime(2024, 1, 2, tzinfo=timezone.utc),
            )

        assert len(articles) == 2
        assert all(isinstance(a, NewsArticleSchema) for a in articles)

    async def test_get_company_news_skips_items_without_url(
        self, provider: FinnhubNewsProvider
    ) -> None:
        items = [_make_item(), {"headline": "No URL", "datetime": 0, "summary": "", "source": "x"}]
        mock_resp = MagicMock()
        mock_resp.json.return_value = items
        mock_resp.raise_for_status = MagicMock()

        with patch.object(provider._client, "get", new=AsyncMock(return_value=mock_resp)):
            articles = await provider.get_company_news(
                "RELIANCE",
                datetime(2024, 1, 1, tzinfo=timezone.utc),
                datetime(2024, 1, 2, tzinfo=timezone.utc),
            )

        assert len(articles) == 1
