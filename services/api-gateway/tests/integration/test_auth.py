from __future__ import annotations

import pytest
from httpx import AsyncClient

TEST_EMAIL = "auth_integration_test@example.com"
TEST_USERNAME = "auth_integ_user"
TEST_PASSWORD = "TestPass123!"
TEST_FULL_NAME = "Auth Test User"


@pytest.mark.asyncio
async def test_register(client: AsyncClient, db_cleanup: list[str]) -> None:
    db_cleanup.append(TEST_EMAIL)
    r = await client.post(
        "/api/v1/auth/register",
        json={
            "email": TEST_EMAIL,
            "username": TEST_USERNAME,
            "password": TEST_PASSWORD,
            "full_name": TEST_FULL_NAME,
        },
    )
    assert r.status_code == 201
    body = r.json()
    assert body["success"] is True
    data = body["data"]
    assert data["user"]["email"] == TEST_EMAIL
    assert data["user"]["username"] == TEST_USERNAME
    assert data["user"]["role"] == "user"
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["expires_in"] == 900


@pytest.mark.asyncio
async def test_register_duplicate_email(client: AsyncClient, db_cleanup: list[str]) -> None:
    db_cleanup.append(TEST_EMAIL)
    payload = {
        "email": TEST_EMAIL,
        "username": TEST_USERNAME,
        "password": TEST_PASSWORD,
    }
    r = await client.post("/api/v1/auth/register", json=payload)
    assert r.status_code == 201

    r = await client.post(
        "/api/v1/auth/register",
        json={**payload, "username": "other_username_xyz"},
    )
    assert r.status_code == 409


@pytest.mark.asyncio
async def test_register_duplicate_username(client: AsyncClient, db_cleanup: list[str]) -> None:
    db_cleanup.append(TEST_EMAIL)
    payload = {
        "email": TEST_EMAIL,
        "username": TEST_USERNAME,
        "password": TEST_PASSWORD,
    }
    r = await client.post("/api/v1/auth/register", json=payload)
    assert r.status_code == 201

    r = await client.post(
        "/api/v1/auth/register",
        json={**payload, "email": "other_xyz@example.com"},
    )
    assert r.status_code == 409


@pytest.mark.asyncio
async def test_login(client: AsyncClient, db_cleanup: list[str]) -> None:
    db_cleanup.append(TEST_EMAIL)
    await client.post(
        "/api/v1/auth/register",
        json={"email": TEST_EMAIL, "username": TEST_USERNAME, "password": TEST_PASSWORD},
    )
    r = await client.post(
        "/api/v1/auth/login",
        json={"email": TEST_EMAIL, "password": TEST_PASSWORD},
    )
    assert r.status_code == 200
    data = r.json()["data"]
    assert data["user"]["email"] == TEST_EMAIL
    assert "access_token" in data
    assert "refresh_token" in data


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient, db_cleanup: list[str]) -> None:
    db_cleanup.append(TEST_EMAIL)
    await client.post(
        "/api/v1/auth/register",
        json={"email": TEST_EMAIL, "username": TEST_USERNAME, "password": TEST_PASSWORD},
    )
    r = await client.post(
        "/api/v1/auth/login",
        json={"email": TEST_EMAIL, "password": "WrongPassword!"},
    )
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_me_requires_auth(client: AsyncClient) -> None:
    r = await client.get("/api/v1/auth/me")
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_refresh_invalid_token(client: AsyncClient) -> None:
    r = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": "this-is-not-a-valid-token"},
    )
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_full_auth_flow(client: AsyncClient, db_cleanup: list[str]) -> None:
    """Full flow: register → me → refresh (rotates token) → old refresh invalid → logout → 401."""
    db_cleanup.append(TEST_EMAIL)

    # Register
    r = await client.post(
        "/api/v1/auth/register",
        json={
            "email": TEST_EMAIL,
            "username": TEST_USERNAME,
            "password": TEST_PASSWORD,
            "full_name": TEST_FULL_NAME,
        },
    )
    assert r.status_code == 201
    data = r.json()["data"]
    access = data["access_token"]
    refresh = data["refresh_token"]

    # Me with valid access token
    r = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {access}"})
    assert r.status_code == 200
    assert r.json()["data"]["email"] == TEST_EMAIL

    # Refresh — rotates both tokens
    r = await client.post("/api/v1/auth/refresh", json={"refresh_token": refresh})
    assert r.status_code == 200
    new_data = r.json()["data"]
    new_access = new_data["access_token"]
    new_refresh = new_data["refresh_token"]
    assert new_refresh != refresh

    # Old refresh token now invalid (session rotated)
    r = await client.post("/api/v1/auth/refresh", json={"refresh_token": refresh})
    assert r.status_code == 401

    # Me with new access token
    r = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {new_access}"})
    assert r.status_code == 200

    # Logout
    r = await client.post("/api/v1/auth/logout", headers={"Authorization": f"Bearer {new_access}"})
    assert r.status_code == 200

    # Me after logout → session revoked → 401
    r = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {new_access}"})
    assert r.status_code == 401
