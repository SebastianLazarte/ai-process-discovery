from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.persistence.base import Base, ExactDecimal, JsonDocument, UTCDateTime, utcnow


class ProcessORM(Base):
    __tablename__ = "processes"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text, default="")
    owner: Mapped[str | None] = mapped_column(String(200), nullable=True)
    executions_per_month: Mapped[int] = mapped_column(Integer)
    hourly_cost: Mapped[Decimal | None] = mapped_column(ExactDecimal, nullable=True)
    # Incremented on every change to the process or its steps; analyses record it.
    version: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow)

    steps: Mapped[list["ProcessStepORM"]] = relationship(
        back_populates="process",
        cascade="all, delete-orphan",
        order_by="ProcessStepORM.position",
    )
    analyses: Mapped[list["AnalysisORM"]] = relationship(
        back_populates="process", cascade="all, delete-orphan", passive_deletes=True
    )


class ProcessStepORM(Base):
    __tablename__ = "process_steps"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    process_id: Mapped[UUID] = mapped_column(ForeignKey("processes.id", ondelete="CASCADE"))
    position: Mapped[int] = mapped_column(Integer)
    name: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text, default="")
    responsible_role: Mapped[str] = mapped_column(String(200), default="")
    tools: Mapped[list[str]] = mapped_column(JsonDocument, default=list)
    input_description: Mapped[str] = mapped_column(Text, default="")
    output_description: Mapped[str] = mapped_column(Text, default="")
    minutes_per_execution: Mapped[Decimal] = mapped_column(ExactDecimal)
    occurrence_rate: Mapped[Decimal] = mapped_column(ExactDecimal)
    repetitiveness: Mapped[str] = mapped_column(String(32))
    rule_clarity: Mapped[str] = mapped_column(String(32))
    input_type: Mapped[str] = mapped_column(String(32))
    exception_rate: Mapped[Decimal | None] = mapped_column(ExactDecimal, nullable=True)
    integration_readiness: Mapped[str] = mapped_column(String(32))
    requires_human_judgement: Mapped[bool] = mapped_column(Boolean, default=False)
    requires_human_approval: Mapped[bool] = mapped_column(Boolean, default=False)
    handles_sensitive_data: Mapped[bool] = mapped_column(Boolean, default=False)
    criticality: Mapped[str] = mapped_column(String(32))
    problems: Mapped[list[str]] = mapped_column(JsonDocument, default=list)

    process: Mapped[ProcessORM] = relationship(back_populates="steps")


class AnalysisORM(Base):
    """Immutable analysis record. Rows are inserted, never updated."""

    __tablename__ = "analyses"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    process_id: Mapped[UUID] = mapped_column(
        ForeignKey("processes.id", ondelete="CASCADE"), index=True
    )
    process_version: Mapped[int] = mapped_column(Integer)
    rules_version: Mapped[str] = mapped_column(String(64))
    prompt_version: Mapped[str | None] = mapped_column(String(64), nullable=True)
    provider: Mapped[str | None] = mapped_column(String(64), nullable=True)
    model: Mapped[str | None] = mapped_column(String(128), nullable=True)
    llm_status: Mapped[str] = mapped_column(String(32))
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow)
    process_snapshot: Mapped[dict[str, Any]] = mapped_column(JsonDocument)
    result: Mapped[dict[str, Any]] = mapped_column(JsonDocument)

    process: Mapped[ProcessORM] = relationship(back_populates="analyses")
    overrides: Mapped[list["OverrideORM"]] = relationship(
        back_populates="analysis",
        cascade="all, delete-orphan",
        order_by="OverrideORM.created_at",
    )


class OverrideORM(Base):
    """A human correction. Keeps the original recommendation next to the new one."""

    __tablename__ = "recommendation_overrides"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    analysis_id: Mapped[UUID] = mapped_column(
        ForeignKey("analyses.id", ondelete="CASCADE"), index=True
    )
    step_id: Mapped[UUID] = mapped_column(Uuid)
    original_method: Mapped[str] = mapped_column(String(32))
    original_human_control: Mapped[str] = mapped_column(String(32))
    new_method: Mapped[str] = mapped_column(String(32))
    new_human_control: Mapped[str] = mapped_column(String(32))
    reason: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow)

    analysis: Mapped[AnalysisORM] = relationship(back_populates="overrides")
