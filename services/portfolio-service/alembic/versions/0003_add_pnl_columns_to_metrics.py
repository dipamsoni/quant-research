"""add cost_basis, unrealized_pnl, realized_pnl to portfolio_metrics

Revision ID: 0003
Revises: 0002
Create Date: 2026-05-21 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0003"
down_revision: Union[str, Sequence[str], None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "portfolio_metrics",
        sa.Column("cost_basis", sa.Numeric(28, 8), nullable=True),
    )
    op.add_column(
        "portfolio_metrics",
        sa.Column("unrealized_pnl", sa.Numeric(28, 8), nullable=True),
    )
    op.add_column(
        "portfolio_metrics",
        sa.Column("realized_pnl", sa.Numeric(28, 8), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("portfolio_metrics", "realized_pnl")
    op.drop_column("portfolio_metrics", "unrealized_pnl")
    op.drop_column("portfolio_metrics", "cost_basis")
