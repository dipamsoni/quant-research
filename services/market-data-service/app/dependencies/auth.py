from __future__ import annotations

from dataclasses import dataclass

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from app.core.config import settings

_http_bearer = HTTPBearer(auto_error=False)


@dataclass
class TokenData:
    user_id: str
    email: str
    role: str


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_http_bearer),
) -> TokenData:
    if credentials is None:
        raise HTTPException(
            status_code=401,
            detail={"code": "UNAUTHORIZED", "message": "Missing authorization header"},
        )
    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM],
        )
    except JWTError:
        raise HTTPException(
            status_code=401,
            detail={"code": "UNAUTHORIZED", "message": "Invalid or expired token"},
        )

    sub = payload.get("sub")
    email = payload.get("email")
    if not sub or not email:
        raise HTTPException(
            status_code=401,
            detail={"code": "UNAUTHORIZED", "message": "Invalid token claims"},
        )

    return TokenData(user_id=sub, email=email, role=payload.get("role", "user"))
