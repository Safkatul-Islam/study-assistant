"""add tags column to documents

Revision ID: 0003
Revises: 0002
Create Date: 2026-03-26

"""

from alembic import op
import sqlalchemy as sa

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "documents",
        sa.Column("tags", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("documents", "tags")
