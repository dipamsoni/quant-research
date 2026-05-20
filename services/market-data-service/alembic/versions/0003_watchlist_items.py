"""watchlist_items table

Revision ID: 0003
Revises: 0002
Create Date: 2026-05-20 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

from alembic import op

revision: str = "0003"
down_revision: str | Sequence[str] | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "watchlist_items",
        sa.Column(
            "id",
            UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("user_id", sa.Text(), nullable=False),
        sa.Column(
            "asset_id",
            UUID(as_uuid=True),
            sa.ForeignKey("assets.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "added_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.UniqueConstraint("user_id", "asset_id", name="uq_watchlist_user_asset"),
    )
    op.create_index(
        "idx_watchlist_user",
        "watchlist_items",
        ["user_id", sa.text("added_at DESC")],
    )


def downgrade() -> None:
    op.drop_index("idx_watchlist_user", table_name="watchlist_items")
    op.drop_table("watchlist_items")
