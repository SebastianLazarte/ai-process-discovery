"""Initial schema

The same tables that create_all built up to 1.3.0. A database created by create_all is
stamped at this revision instead of running it
(docs/runbook/production.md). The column types are the storage types of the models, so
money and hours stay exact on both engines (ADR 0002).

Revision ID: 0001
Revises:
Create Date: 2026-10-16
"""

from collections.abc import Sequence
from typing import Any

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

from app.models.persistence.base import ExactDecimal, UTCDateTime

# Alembic reads these names from the module, so they are its public interface.
__all__ = ["branch_labels", "depends_on", "down_revision", "downgrade", "revision", "upgrade"]

revision: str = "0001"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _json() -> sa.types.TypeEngine[Any]:
    return sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), "postgresql")


def upgrade() -> None:
    op.create_table(
        "processes",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("owner", sa.String(length=200), nullable=True),
        sa.Column("executions_per_month", sa.Integer(), nullable=False),
        sa.Column("hourly_cost", ExactDecimal(), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("created_at", UTCDateTime(timezone=True), nullable=False),
        sa.Column("updated_at", UTCDateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "analyses",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("process_id", sa.Uuid(), nullable=False),
        sa.Column("process_version", sa.Integer(), nullable=False),
        sa.Column("rules_version", sa.String(length=64), nullable=False),
        sa.Column("prompt_version", sa.String(length=64), nullable=True),
        sa.Column("provider", sa.String(length=64), nullable=True),
        sa.Column("model", sa.String(length=128), nullable=True),
        sa.Column("llm_status", sa.String(length=32), nullable=False),
        sa.Column("created_at", UTCDateTime(timezone=True), nullable=False),
        sa.Column("process_snapshot", _json(), nullable=False),
        sa.Column("result", _json(), nullable=False),
        sa.ForeignKeyConstraint(["process_id"], ["processes.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_analyses_process_id", "analyses", ["process_id"], unique=False)
    op.create_table(
        "process_steps",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("process_id", sa.Uuid(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("responsible_role", sa.String(length=200), nullable=False),
        sa.Column("tools", _json(), nullable=False),
        sa.Column("input_description", sa.Text(), nullable=False),
        sa.Column("output_description", sa.Text(), nullable=False),
        sa.Column("minutes_per_execution", ExactDecimal(), nullable=False),
        sa.Column("occurrence_rate", ExactDecimal(), nullable=False),
        sa.Column("repetitiveness", sa.String(length=32), nullable=False),
        sa.Column("rule_clarity", sa.String(length=32), nullable=False),
        sa.Column("input_type", sa.String(length=32), nullable=False),
        sa.Column("exception_rate", ExactDecimal(), nullable=True),
        sa.Column("integration_readiness", sa.String(length=32), nullable=False),
        sa.Column("requires_human_judgement", sa.Boolean(), nullable=False),
        sa.Column("requires_human_approval", sa.Boolean(), nullable=False),
        sa.Column("handles_sensitive_data", sa.Boolean(), nullable=False),
        sa.Column("criticality", sa.String(length=32), nullable=False),
        sa.Column("problems", _json(), nullable=False),
        sa.ForeignKeyConstraint(["process_id"], ["processes.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "recommendation_overrides",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("analysis_id", sa.Uuid(), nullable=False),
        sa.Column("step_id", sa.Uuid(), nullable=False),
        sa.Column("original_method", sa.String(length=32), nullable=False),
        sa.Column("original_human_control", sa.String(length=32), nullable=False),
        sa.Column("new_method", sa.String(length=32), nullable=False),
        sa.Column("new_human_control", sa.String(length=32), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("created_at", UTCDateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["analysis_id"], ["analyses.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_recommendation_overrides_analysis_id",
        "recommendation_overrides",
        ["analysis_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_recommendation_overrides_analysis_id", "recommendation_overrides")
    op.drop_table("recommendation_overrides")
    op.drop_table("process_steps")
    op.drop_index("ix_analyses_process_id", "analyses")
    op.drop_table("analyses")
    op.drop_table("processes")
