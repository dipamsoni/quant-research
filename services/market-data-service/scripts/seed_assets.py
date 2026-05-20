#!/usr/bin/env python3
"""Idempotent asset seeder. Run from the service root:

    uv run python scripts/seed_assets.py
"""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

# Allow `import app.*` when running from repo root or service dir.
_SERVICE_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_SERVICE_ROOT))

import structlog
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.core.database import AsyncSessionLocal
from app.core.logging import configure_logging
from app.models.asset import Asset

configure_logging()
logger = structlog.get_logger()

_SEED_FILE = Path(__file__).parent / "assets_seed_data.json"


async def main() -> None:
    raw = json.loads(_SEED_FILE.read_bytes().decode("utf-8", errors="replace"))
    assets: list[dict] = raw["assets"]
    logger.info("seed_start", total=len(assets), source=str(_SEED_FILE))

    async with AsyncSessionLocal() as db:
        for row in assets:
            stmt = (
                pg_insert(Asset)
                .values(**row)
                .on_conflict_do_update(
                    index_elements=["symbol"],
                    set_={
                        "name": row["name"],
                        "asset_type": row["asset_type"],
                        "exchange": row["exchange"],
                        "currency": row["currency"],
                        "sector": row["sector"],
                        "industry": row["industry"],
                        "is_active": True,
                    },
                )
            )
            await db.execute(stmt)
        await db.commit()

    logger.info("seed_complete", upserted=len(assets))


if __name__ == "__main__":
    asyncio.run(main())
