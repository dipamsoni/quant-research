"""users and sessions

Revision ID: c03d76e67303
Revises:
Create Date: 2026-05-19 08:10:43.128124

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import INET, UUID

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c03d76e67303"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS citext")

    op.create_table(
        "users",
        sa.Column(
            "id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")
        ),
        sa.Column("email", sa.Text().with_variant(sa.Text(), "postgresql"), nullable=False),
        sa.Column("username", sa.Text().with_variant(sa.Text(), "postgresql"), nullable=False),
        sa.Column("hashed_password", sa.Text(), nullable=False),
        sa.Column("full_name", sa.Text(), nullable=True),
        sa.Column("role", sa.String(), nullable=False, server_default="user"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("TRUE")),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
    )
    # Use raw DDL for CITEXT columns so the extension type is applied correctly
    op.execute("ALTER TABLE users ALTER COLUMN email TYPE CITEXT")
    op.execute("ALTER TABLE users ALTER COLUMN username TYPE CITEXT")
    op.execute("ALTER TABLE users ADD CONSTRAINT users_email_key UNIQUE (email)")
    op.execute("ALTER TABLE users ADD CONSTRAINT users_username_key UNIQUE (username)")
    op.create_index("idx_users_email", "users", ["email"])

    op.create_table(
        "sessions",
        sa.Column(
            "id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")
        ),
        sa.Column(
            "user_id",
            UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("refresh_token_hash", sa.Text(), nullable=False),
        sa.Column("ip_address", INET(), nullable=True),
        sa.Column("device_info", sa.Text(), nullable=True),
        sa.Column("expires_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
    )
    op.create_index("idx_sessions_user_id", "sessions", ["user_id"])


def downgrade() -> None:
    op.drop_index("idx_sessions_user_id", table_name="sessions")
    op.drop_table("sessions")
    op.drop_index("idx_users_email", table_name="users")
    op.drop_table("users")
