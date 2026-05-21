from __future__ import annotations

import asyncio
from concurrent.futures import ThreadPoolExecutor

import pytest

from app.core.config import settings


@pytest.fixture
def portfolio_cleanup() -> list[str]:
    """Yields a list; append portfolio id strings to delete after the test."""
    ids: list[str] = []
    yield ids
    if not ids:
        return

    async def _cleanup() -> None:
        import asyncpg

        dsn = settings.DATABASE_URL.replace("postgresql+asyncpg", "postgresql")
        conn = await asyncpg.connect(dsn)
        try:
            await conn.execute(
                "DELETE FROM portfolios WHERE id = ANY($1::uuid[])",
                [asyncpg.pgproto.pgproto.UUID(i) for i in ids],
            )
        finally:
            await conn.close()

    with ThreadPoolExecutor(max_workers=1) as pool:
        pool.submit(asyncio.run, _cleanup()).result()
