from __future__ import annotations

import hashlib
import secrets
import uuid
from datetime import UTC, datetime, timedelta

import bcrypt as _bcrypt
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.session import Session
from app.models.user import User
from app.repositories import users as user_repo
from app.schemas.auth import LoginRequest, RegisterRequest


def hash_password(password: str) -> str:
    return _bcrypt.hashpw(password.encode(), _bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    return _bcrypt.checkpw(plain.encode(), hashed.encode())


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def create_access_token(
    user_id: uuid.UUID,
    session_id: uuid.UUID,
    email: str,
    role: str,
) -> str:
    expire = datetime.now(UTC) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": str(user_id),
        "sid": str(session_id),
        "email": email,
        "role": role,
        "exp": expire,
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str, *, verify_exp: bool = True) -> dict:  # type: ignore[type-arg]
    options: dict[str, bool] = {} if verify_exp else {"verify_exp": False}
    return jwt.decode(  # type: ignore[return-value]
        token,
        settings.JWT_SECRET,
        algorithms=[settings.JWT_ALGORITHM],
        options=options,
    )


async def _create_session(
    db: AsyncSession,
    user_id: uuid.UUID,
    *,
    ip_address: str | None = None,
    device_info: str | None = None,
) -> tuple[Session, str]:
    raw_refresh = secrets.token_urlsafe(32)
    token_hash = _hash_token(raw_refresh)
    expires_at = datetime.now(UTC) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    session = Session(
        user_id=user_id,
        refresh_token_hash=token_hash,
        ip_address=ip_address,
        device_info=device_info,
        expires_at=expires_at,
    )
    db.add(session)
    await db.flush()
    await db.refresh(session)
    return session, raw_refresh


async def register_user(
    db: AsyncSession,
    req: RegisterRequest,
    *,
    ip_address: str | None = None,
    device_info: str | None = None,
) -> tuple[User, str, str]:
    if await user_repo.get_by_email(db, req.email):
        raise ValueError("Email already registered")
    if await user_repo.get_by_username(db, req.username):
        raise ValueError("Username already taken")

    user = await user_repo.create(
        db,
        email=req.email,
        username=req.username,
        hashed_password=hash_password(req.password),
        full_name=req.full_name,
    )
    session, raw_refresh = await _create_session(
        db, user.id, ip_address=ip_address, device_info=device_info
    )
    access_token = create_access_token(user.id, session.id, user.email, user.role)
    await db.commit()
    await db.refresh(user)
    return user, access_token, raw_refresh


async def authenticate(
    db: AsyncSession,
    req: LoginRequest,
    *,
    ip_address: str | None = None,
    device_info: str | None = None,
) -> tuple[User, str, str]:
    user = await user_repo.get_by_email(db, req.email)
    if not user or not verify_password(req.password, user.hashed_password):
        raise ValueError("Invalid email or password")
    if not user.is_active:
        raise ValueError("Account is inactive")

    session, raw_refresh = await _create_session(
        db, user.id, ip_address=ip_address, device_info=device_info
    )
    access_token = create_access_token(user.id, session.id, user.email, user.role)
    await db.commit()
    await db.refresh(user)
    return user, access_token, raw_refresh


async def refresh_tokens(
    db: AsyncSession,
    raw_refresh: str,
    *,
    ip_address: str | None = None,
    device_info: str | None = None,
) -> tuple[User, str, str]:
    token_hash = _hash_token(raw_refresh)
    result = await db.execute(select(Session).where(Session.refresh_token_hash == token_hash))
    session = result.scalar_one_or_none()

    if session is None:
        raise ValueError("Invalid refresh token")

    expires_at: datetime = session.expires_at  # type: ignore[assignment]
    if expires_at < datetime.now(UTC):
        await db.delete(session)
        await db.commit()
        raise ValueError("Refresh token expired")

    user = await user_repo.get_by_id(db, session.user_id)
    if not user or not user.is_active:
        raise ValueError("User not found or inactive")

    await db.delete(session)
    new_session, new_raw_refresh = await _create_session(
        db, user.id, ip_address=ip_address, device_info=device_info
    )
    access_token = create_access_token(user.id, new_session.id, user.email, user.role)
    await db.commit()
    await db.refresh(user)
    return user, access_token, new_raw_refresh


async def revoke_session(db: AsyncSession, session_id: uuid.UUID) -> None:
    session = await db.get(Session, session_id)
    if session:
        await db.delete(session)
        await db.commit()


async def revoke_session_from_token(db: AsyncSession, token: str) -> None:
    """Extract session ID from token and revoke it. Does not verify expiry."""
    try:
        payload = decode_access_token(token, verify_exp=False)
        sid = payload.get("sid")
        if sid:
            await revoke_session(db, uuid.UUID(sid))
    except (JWTError, ValueError):
        pass
