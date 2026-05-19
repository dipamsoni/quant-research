from __future__ import annotations

import uuid

from pydantic import BaseModel, ConfigDict, EmailStr


class APISuccess[T](BaseModel):
    success: bool = True
    data: T


class RegisterRequest(BaseModel):
    email: EmailStr
    username: str
    password: str
    full_name: str | None = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str
    username: str
    full_name: str | None
    role: str


class TokenResponse(BaseModel):
    user: UserResponse
    access_token: str
    refresh_token: str
    expires_in: int
