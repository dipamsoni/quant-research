from __future__ import annotations

import pytest_asyncio
from sqlalchemy import delete

from app.core.database import AsyncSessionLocal
from app.models.user import User


@pytest_asyncio.fixture
async def db_cleanup() -> list[str]:
    """Yields a list; append email strings to delete those users after the test.
    Sessions are cascade-deleted via FK when the user is deleted.
    """
    emails: list[str] = []
    yield emails  # type: ignore[misc]
    if emails:
        async with AsyncSessionLocal() as db:
            await db.execute(delete(User).where(User.email.in_(emails)))
            await db.commit()
