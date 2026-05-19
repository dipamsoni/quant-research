from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.auth import (
    APISuccess,
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)
from app.services import auth as auth_service

router = APIRouter(prefix="/auth", tags=["auth"])

_ACCESS_EXPIRES_SECONDS = 900  # 15 min


def _token_resp(user: User, access: str, refresh: str) -> APISuccess[TokenResponse]:
    return APISuccess(
        data=TokenResponse(
            user=UserResponse.model_validate(user),
            access_token=access,
            refresh_token=refresh,
            expires_in=_ACCESS_EXPIRES_SECONDS,
        )
    )


@router.post(
    "/register",
    status_code=status.HTTP_201_CREATED,
    response_model=APISuccess[TokenResponse],
)
async def register(
    req: RegisterRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> APISuccess[TokenResponse]:
    try:
        user, access, refresh = await auth_service.register_user(
            db,
            req,
            ip_address=request.client.host if request.client else None,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": "CONFLICT", "message": str(exc)},
        )
    return _token_resp(user, access, refresh)


@router.post("/login", response_model=APISuccess[TokenResponse])
async def login(
    req: LoginRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> APISuccess[TokenResponse]:
    try:
        user, access, refresh = await auth_service.authenticate(
            db,
            req,
            ip_address=request.client.host if request.client else None,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "UNAUTHORIZED", "message": str(exc)},
        )
    return _token_resp(user, access, refresh)


@router.post("/refresh", response_model=APISuccess[TokenResponse])
async def refresh(
    req: RefreshRequest,
    db: AsyncSession = Depends(get_db),
) -> APISuccess[TokenResponse]:
    try:
        user, access, new_refresh = await auth_service.refresh_tokens(db, req.refresh_token)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "UNAUTHORIZED", "message": str(exc)},
        )
    return _token_resp(user, access, new_refresh)


@router.post("/logout")
async def logout(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> dict:  # type: ignore[type-arg]
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "UNAUTHORIZED", "message": "Missing authorization header"},
        )
    token = auth_header[7:]
    await auth_service.revoke_session_from_token(db, token)
    return {"success": True, "data": {"message": "Logged out successfully"}}


@router.get("/me", response_model=APISuccess[UserResponse])
async def me(
    current_user: User = Depends(get_current_user),
) -> APISuccess[UserResponse]:
    return APISuccess(data=UserResponse.model_validate(current_user))
