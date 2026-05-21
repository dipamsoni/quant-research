"""create portfolio tables

Revision ID: 0001
Revises:
Create Date: 2026-05-20 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "portfolios",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("base_currency", sa.String(10), nullable=False, server_default="INR"),
        sa.Column("risk_profile", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
    )
    op.create_index("idx_portfolios_user_id", "portfolios", ["user_id"])

    op.create_table(
        "holdings",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("portfolio_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("asset_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("quantity", sa.Numeric(28, 8), nullable=False),
        sa.Column("avg_price", sa.Numeric(20, 8), nullable=False),
        sa.Column("market_value", sa.Numeric(28, 8), nullable=True),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.ForeignKeyConstraint(["portfolio_id"], ["portfolios.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("portfolio_id", "asset_id", name="uq_holdings_portfolio_asset"),
    )
    op.create_index("idx_holdings_portfolio_id", "holdings", ["portfolio_id"])

    op.create_table(
        "transactions",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("portfolio_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("asset_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("transaction_type", sa.String(10), nullable=False),
        sa.Column("quantity", sa.Numeric(28, 8), nullable=False),
        sa.Column("price", sa.Numeric(20, 8), nullable=False),
        sa.Column("fees", sa.Numeric(20, 8), nullable=False, server_default="0"),
        sa.Column("executed_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.ForeignKeyConstraint(["portfolio_id"], ["portfolios.id"], ondelete="CASCADE"),
    )
    op.create_index("idx_tx_portfolio", "transactions", ["portfolio_id"])
    op.create_index("idx_tx_executed", "transactions", ["executed_at"], postgresql_ops={"executed_at": "DESC"})

    op.create_table(
        "portfolio_metrics",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("portfolio_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("total_value", sa.Numeric(28, 8), nullable=False),
        sa.Column("daily_return", sa.Numeric(10, 8), nullable=True),
        sa.Column("sharpe_ratio", sa.Numeric(10, 4), nullable=True),
        sa.Column("max_drawdown", sa.Numeric(10, 8), nullable=True),
        sa.Column("volatility", sa.Numeric(10, 8), nullable=True),
        sa.Column("beta", sa.Numeric(10, 6), nullable=True),
        sa.Column("alpha", sa.Numeric(10, 8), nullable=True),
        sa.ForeignKeyConstraint(["portfolio_id"], ["portfolios.id"], ondelete="CASCADE"),
        sa.UniqueConstraint(
            "portfolio_id", "date", name="uq_portfolio_metrics_portfolio_date"
        ),
    )
    op.create_index("idx_portfolio_metrics_portfolio_id", "portfolio_metrics", ["portfolio_id"])


def downgrade() -> None:
    op.drop_table("portfolio_metrics")
    op.drop_table("transactions")
    op.drop_table("holdings")
    op.drop_table("portfolios")
