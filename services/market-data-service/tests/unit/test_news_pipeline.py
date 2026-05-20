"""Unit tests for news_pipeline.

All DB and Redis calls are mocked — no real infrastructure needed.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.pipelines.news_pipeline import (
    _BACKFILL_HOURS,
    _get_last_ingested,
    _set_last_ingested,
    ingest_news_for_symbol,
)
from app.providers.finnhub_news_provider import NewsArticleSchema


def _article(url: str = "https://example.com/1", symbol: str = "RELIANCE") -> NewsArticleSchema:
    return NewsArticleSchema(
        title="Test headline",
        content="Body text.",
        source="Reuters",
        url=url,
        published_at=datetime(2024, 6, 1, 12, tzinfo=timezone.utc),
        symbols=[symbol],
    )


@pytest.fixture
def mock_redis() -> MagicMock:
    r = MagicMock()
    r.get = AsyncMock(return_value=None)
    r.set = AsyncMock()
    return r


class TestGetSetLastIngested:
    async def test_get_returns_none_when_key_missing(self, mock_redis: MagicMock) -> None:
        mock_redis.get.return_value = None
        with patch("app.pipelines.news_pipeline.get_redis", return_value=mock_redis):
            result = await _get_last_ingested("RELIANCE")
        assert result is None

    async def test_get_parses_iso_string(self, mock_redis: MagicMock) -> None:
        dt = datetime(2024, 6, 1, 0, 0, tzinfo=timezone.utc)
        mock_redis.get.return_value = dt.isoformat()
        with patch("app.pipelines.news_pipeline.get_redis", return_value=mock_redis):
            result = await _get_last_ingested("RELIANCE")
        assert result == dt

    async def test_set_stores_iso_string(self, mock_redis: MagicMock) -> None:
        dt = datetime(2024, 6, 1, 0, 0, tzinfo=timezone.utc)
        with patch("app.pipelines.news_pipeline.get_redis", return_value=mock_redis):
            await _set_last_ingested("RELIANCE", dt)
        mock_redis.set.assert_awaited_once_with("news:last_ingested:RELIANCE", dt.isoformat())


class TestIngestNewsForSymbol:
    async def test_first_run_uses_24h_backfill(self, mock_redis: MagicMock) -> None:
        articles = [_article()]
        mock_provider = MagicMock()
        mock_provider.get_company_news = AsyncMock(return_value=articles)

        captured: list[datetime] = []

        async def _fake_get(sym: str) -> datetime | None:
            return None

        async def _fake_upsert(arts):  # type: ignore[no-untyped-def]
            return len(arts)

        with (
            patch("app.pipelines.news_pipeline.get_redis", return_value=mock_redis),
            patch("app.pipelines.news_pipeline._get_last_ingested", side_effect=_fake_get),
            patch("app.pipelines.news_pipeline._set_last_ingested", new=AsyncMock()),
            patch("app.pipelines.news_pipeline._upsert_articles", side_effect=_fake_upsert),
        ):
            now_before = datetime.now(tz=timezone.utc)
            await ingest_news_for_symbol("RELIANCE", mock_provider)
            now_after = datetime.now(tz=timezone.utc)

        call_args = mock_provider.get_company_news.call_args
        from_dt: datetime = call_args[0][1]
        expected_earliest = now_before - timedelta(hours=_BACKFILL_HOURS)
        assert from_dt >= expected_earliest
        assert from_dt <= now_after

    async def test_subsequent_run_uses_last_ingested(self, mock_redis: MagicMock) -> None:
        last = datetime(2024, 6, 1, 10, tzinfo=timezone.utc)
        articles = [_article()]
        mock_provider = MagicMock()
        mock_provider.get_company_news = AsyncMock(return_value=articles)

        async def _fake_get(sym: str) -> datetime | None:
            return last

        with (
            patch("app.pipelines.news_pipeline.get_redis", return_value=mock_redis),
            patch("app.pipelines.news_pipeline._get_last_ingested", side_effect=_fake_get),
            patch("app.pipelines.news_pipeline._set_last_ingested", new=AsyncMock()),
            patch("app.pipelines.news_pipeline._upsert_articles", return_value=1),
        ):
            await ingest_news_for_symbol("RELIANCE", mock_provider)

        call_args = mock_provider.get_company_news.call_args
        from_dt: datetime = call_args[0][1]
        assert from_dt == last

    async def test_provider_error_returns_zero(self, mock_redis: MagicMock) -> None:
        mock_provider = MagicMock()
        mock_provider.get_company_news = AsyncMock(side_effect=Exception("API down"))

        async def _fake_get(sym: str) -> datetime | None:
            return None

        with (
            patch("app.pipelines.news_pipeline.get_redis", return_value=mock_redis),
            patch("app.pipelines.news_pipeline._get_last_ingested", side_effect=_fake_get),
            patch("app.pipelines.news_pipeline._set_last_ingested", new=AsyncMock()),
        ):
            inserted, rate_limited = await ingest_news_for_symbol("RELIANCE", mock_provider)

        assert inserted == 0
        assert rate_limited is False

    async def test_dedup_returns_inserted_count(self, mock_redis: MagicMock) -> None:
        articles = [_article("https://a.com/1"), _article("https://a.com/2")]
        mock_provider = MagicMock()
        mock_provider.get_company_news = AsyncMock(return_value=articles)

        async def _fake_get(sym: str) -> datetime | None:
            return None

        with (
            patch("app.pipelines.news_pipeline.get_redis", return_value=mock_redis),
            patch("app.pipelines.news_pipeline._get_last_ingested", side_effect=_fake_get),
            patch("app.pipelines.news_pipeline._set_last_ingested", new=AsyncMock()),
            patch("app.pipelines.news_pipeline._upsert_articles", return_value=1),
        ):
            inserted, rate_limited = await ingest_news_for_symbol("RELIANCE", mock_provider)

        assert inserted == 1
        assert rate_limited is False
