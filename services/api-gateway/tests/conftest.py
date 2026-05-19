from unittest.mock import AsyncMock, patch

import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.core.database import engine
from app.main import app


@pytest_asyncio.fixture(scope="session")
async def client() -> AsyncClient:
    # Mock Redis: auth tests don't use it, and real async pool cleanup
    # races with event-loop teardown in pytest-asyncio 0.24.
    with (
        patch("app.main.init_redis", new_callable=AsyncMock),
        patch("app.main.close_redis", new_callable=AsyncMock),
    ):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            yield ac
    # Dispose SQLAlchemy pool while the event loop is still running.
    # Without this, asyncpg background tasks fire after loop close → "Event loop is closed".
    await engine.dispose()
