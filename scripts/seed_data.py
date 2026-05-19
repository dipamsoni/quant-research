#!/usr/bin/env python3
"""Seed test user into the database.

Run from repo root (requires api-gateway venv):
    cd services/api-gateway && uv run python ../../scripts/seed_data.py

Or with explicit DATABASE_URL:
    DATABASE_URL=postgresql+asyncpg://user:pass@localhost/quantos \
        uv run --directory services/api-gateway python ../../scripts/seed_data.py
"""

from __future__ import annotations

import asyncio
import os
import sys

import asyncpg
import bcrypt

TEST_EMAIL = "test@quantos.local"
TEST_USERNAME = "testuser"
TEST_PASSWORD = "testpass123"

_DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost:5432/quantos",
)
# asyncpg uses postgresql:// not postgresql+asyncpg://
PG_DSN = _DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")


async def seed() -> None:
    try:
        conn = await asyncpg.connect(PG_DSN)
    except Exception as exc:
        print(f"ERROR: cannot connect to database: {exc}", file=sys.stderr)
        print(f"  DSN: {PG_DSN}", file=sys.stderr)
        sys.exit(1)

    try:
        existing = await conn.fetchrow(
            "SELECT id FROM users WHERE email = $1", TEST_EMAIL
        )
        if existing:
            print(f"User already exists: {TEST_EMAIL} — skipping.")
            return

        hashed = bcrypt.hashpw(TEST_PASSWORD.encode(), bcrypt.gensalt()).decode()
        await conn.execute(
            """
            INSERT INTO users (email, username, hashed_password, role, is_active)
            VALUES ($1, $2, $3, 'user', TRUE)
            """,
            TEST_EMAIL,
            TEST_USERNAME,
            hashed,
        )
        print(f"Created: {TEST_EMAIL} / {TEST_PASSWORD}")
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(seed())
