from __future__ import annotations

import asyncio
from concurrent.futures import ThreadPoolExecutor

import pytest

from app.core.config import settings


@pytest.fixture
def asset_cleanup() -> list[str]:
    """Yields a list; append symbol strings to delete those assets after the test.
    ohlcv_candles are cascade-deleted via FK when the asset is deleted.
    """
    symbols: list[str] = []
    yield symbols
    if not symbols:
        return

    async def _cleanup() -> None:
        import asyncpg  # optional dep — only needed for integration tests

        dsn = settings.DATABASE_URL.replace("postgresql+asyncpg", "postgresql")
        conn = await asyncpg.connect(dsn)
        try:
            await conn.execute(
                "DELETE FROM assets WHERE symbol = ANY($1::text[])",
                symbols,
            )
        finally:
            await conn.close()

    with ThreadPoolExecutor(max_workers=1) as pool:
        pool.submit(asyncio.run, _cleanup()).result()
