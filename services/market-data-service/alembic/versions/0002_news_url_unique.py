"""news_articles: unique index on url for dedup

Revision ID: 0002
Revises: 0001
Create Date: 2026-05-20 00:00:00.000000

"""

from collections.abc import Sequence

from alembic import op

revision: str = "0002"
down_revision: str | Sequence[str] | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_index("idx_news_url", "news_articles", ["url"], unique=True)


def downgrade() -> None:
    op.drop_index("idx_news_url", table_name="news_articles")
