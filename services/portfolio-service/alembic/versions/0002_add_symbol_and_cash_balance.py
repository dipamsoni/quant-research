"""add symbol to holdings and cash_balance to portfolios

Revision ID: 0002
Revises: 0001
Create Date: 2026-05-21 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0002"
down_revision: Union[str, Sequence[str], None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "holdings",
        sa.Column("symbol", sa.String(50), nullable=False, server_default="UNKNOWN"),
    )
    op.add_column(
        "portfolios",
        sa.Column(
            "cash_balance",
            sa.Numeric(28, 8),
            nullable=False,
            server_default="0",
        ),
    )


def downgrade() -> None:
    op.drop_column("holdings", "symbol")
    op.drop_column("portfolios", "cash_balance")
