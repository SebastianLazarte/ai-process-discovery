"""Usage counters

Daily usage counters of the public demo: a UTC day, an event and a count, with nothing that
points back to a visitor, kept after the purge (ADR 0020, RS-114).

Revision ID: 0003
Revises: 0002
Create Date: 2026-11-08
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# Alembic reads these names from the module, so they are its public interface.
__all__ = ["branch_labels", "depends_on", "down_revision", "downgrade", "revision", "upgrade"]

revision: str = "0003"
down_revision: str | Sequence[str] | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "usage_counters",
        sa.Column("day", sa.Date(), nullable=False),
        sa.Column("event", sa.String(length=32), nullable=False),
        sa.Column("count", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("day", "event"),
    )


def downgrade() -> None:
    op.drop_table("usage_counters")
