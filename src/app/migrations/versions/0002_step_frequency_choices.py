"""Step frequency choices

The plain-word choice behind the occurrence and exception rates of a step (RS-115). Expand
only: both columns are nullable, and an existing step keeps its rate as an exact figure
with no choice, which the previous release ignores.

Revision ID: 0002
Revises: 0001
Create Date: 2026-11-07
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# Alembic reads these names from the module, so they are its public interface.
__all__ = ["branch_labels", "depends_on", "down_revision", "downgrade", "revision", "upgrade"]

revision: str = "0002"
down_revision: str | Sequence[str] | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("process_steps") as batch_op:
        batch_op.add_column(sa.Column("frequency", sa.String(length=32), nullable=True))
        batch_op.add_column(sa.Column("exception_frequency", sa.String(length=32), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("process_steps") as batch_op:
        batch_op.drop_column("exception_frequency")
        batch_op.drop_column("frequency")
