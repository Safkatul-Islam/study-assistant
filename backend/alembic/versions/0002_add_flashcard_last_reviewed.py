"""add last_reviewed_at to flashcards

Revision ID: 0002
Revises: 0001
Create Date: 2026-03-25

"""

from alembic import op
import sqlalchemy as sa

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "flashcards",
        sa.Column("last_reviewed_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("flashcards", "last_reviewed_at")
