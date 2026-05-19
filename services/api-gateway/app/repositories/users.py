from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


async def get_by_email(db: AsyncSession, email: str) -> User | None:
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def get_by_username(db: AsyncSession, username: str) -> User | None:
    result = await db.execute(select(User).where(User.username == username))
    return result.scalar_one_or_none()


async def get_by_id(db: AsyncSession, user_id: uuid.UUID) -> User | None:
    return await db.get(User, user_id)


async def create(
    db: AsyncSession,
    *,
    email: str,
    username: str,
    hashed_password: str,
    full_name: str | None = None,
) -> User:
    user = User(
        email=email,
        username=username,
        hashed_password=hashed_password,
        full_name=full_name,
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)
    return user
