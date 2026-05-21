from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

import pytest
from httpx import ASGITransport, AsyncClient
from jose import jwt
from sqlalchemy import delete

from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.main import app
from app.models.portfolio import Portfolio

TEST_USER_ID = uuid.uuid4()
OTHER_USER_ID = uuid.uuid4()


def _make_token(user_id: uuid.UUID, email: str) -> str:
    return jwt.encode(
        {
            "sub": str(user_id),
            "email": email,
            "role": "user",
            "exp": datetime.now(timezone.utc) + timedelta(hours=1),
        },
        settings.JWT_SECRET,
        algorithm=settings.JWT_ALGORITHM,
    )


@pytest.fixture(scope="module")
async def client():
    """AsyncClient authenticated as TEST_USER via a real signed JWT token."""
    token = _make_token(TEST_USER_ID, "integration-test@example.com")
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
        headers={"Authorization": f"Bearer {token}"},
    ) as c:
        yield c


@pytest.fixture(scope="module")
async def other_client():
    """AsyncClient authenticated as OTHER_USER via a real signed JWT token."""
    token = _make_token(OTHER_USER_ID, "other@example.com")
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
        headers={"Authorization": f"Bearer {token}"},
    ) as c:
        yield c


@pytest.fixture(scope="module")
def cleanup_ids() -> list[str]:
    """Accumulate portfolio IDs to delete after the module."""
    return []


@pytest.fixture(scope="module", autouse=True)
async def _cleanup(cleanup_ids: list[str]):
    yield
    if not cleanup_ids:
        return
    async with AsyncSessionLocal() as session:
        for pid in cleanup_ids:
            await session.execute(
                delete(Portfolio).where(Portfolio.id == uuid.UUID(pid))
            )
        await session.commit()
