from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies.auth import TokenData, get_current_user
from app.models.news import NewsArticle
from app.schemas.market import APISuccess, NewsResponse

router = APIRouter(prefix="/api/v1/market", tags=["news"])

_MAX_LIMIT = 100


@router.get("/news", response_model=APISuccess[list[NewsResponse]])
async def get_news(
    symbol: Annotated[str, Query(description="Asset symbol, e.g. RELIANCE")],
    limit: Annotated[int, Query(ge=1, le=_MAX_LIMIT)] = 50,
    hours: Annotated[int, Query(ge=1, le=168, description="Look-back window in hours (default 24)")] = 24,
    db: AsyncSession = Depends(get_db),
    _user: TokenData = Depends(get_current_user),
) -> APISuccess[list[NewsResponse]]:
    """Return news articles tagged with *symbol* published within the last *hours* hours."""
    since = datetime.now(tz=timezone.utc) - timedelta(hours=hours)
    stmt = (
        select(NewsArticle)
        .where(
            NewsArticle.symbols.contains([symbol]),
            NewsArticle.published_at >= since,
        )
        .order_by(NewsArticle.published_at.desc())
        .limit(limit)
    )
    result = await db.execute(stmt)
    articles = list(result.scalars().all())
    return APISuccess(data=[NewsResponse.model_validate(a) for a in articles])
