from __future__ import annotations

import uuid
from datetime import UTC, datetime

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.session import Session
from app.models.user import User
from app.repositories import users as user_repo
from app.services.auth import decode_access_token

http_bearer = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(http_bearer),
    db: AsyncSession = Depends(get_db),
) -> User:
    if credentials is None:
        raise HTTPException(
            status_code=401,
            detail={"code": "UNAUTHORIZED", "message": "Missing authorization header"},
        )
    try:
        payload = decode_access_token(credentials.credentials)
    except JWTError:
        raise HTTPException(
            status_code=401,
            detail={"code": "UNAUTHORIZED", "message": "Invalid or expired token"},
        )

    sub = payload.get("sub")
    sid = payload.get("sid")
    if not sub or not sid:
        raise HTTPException(
            status_code=401,
            detail={"code": "UNAUTHORIZED", "message": "Invalid token claims"},
        )

    try:
        session_id = uuid.UUID(sid)
        user_id = uuid.UUID(sub)
    except ValueError:
        raise HTTPException(
            status_code=401,
            detail={"code": "UNAUTHORIZED", "message": "Invalid token claims"},
        )

    session = await db.get(Session, session_id)
    if session is None:
        raise HTTPException(
            status_code=401,
            detail={"code": "UNAUTHORIZED", "message": "Session revoked or not found"},
        )

    expires_at: datetime = session.expires_at  # type: ignore[assignment]
    if expires_at < datetime.now(UTC):
        raise HTTPException(
            status_code=401,
            detail={"code": "UNAUTHORIZED", "message": "Session expired"},
        )

    if session.user_id != user_id:
        raise HTTPException(
            status_code=401,
            detail={"code": "UNAUTHORIZED", "message": "Token/session mismatch"},
        )

    user = await user_repo.get_by_id(db, user_id)
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=401,
            detail={"code": "UNAUTHORIZED", "message": "User not found or inactive"},
        )

    return user  # type: ignore[return-value]
