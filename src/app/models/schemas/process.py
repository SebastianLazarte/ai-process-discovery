"""HTTP contracts for processes and steps. Decimals travel as JSON strings."""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.domain.enums import InputType, IntegrationReadiness, Level


class _Schema(BaseModel):
    model_config = ConfigDict(extra="forbid")


class StepFields(_Schema):
    name: str = Field(min_length=1, max_length=200)
    description: str = ""
    responsible_role: str = Field(default="", max_length=200)
    tools: list[str] = Field(default_factory=list)
    input_description: str = ""
    output_description: str = ""
    minutes_per_execution: Decimal = Field(ge=0, examples=["4.0"])
    occurrence_rate: Decimal = Field(default=Decimal(1), ge=0, le=1)
    repetitiveness: Level = Level.UNKNOWN
    rule_clarity: Level = Level.UNKNOWN
    input_type: InputType = InputType.UNKNOWN
    exception_rate: Decimal | None = Field(default=None, ge=0, le=1)
    integration_readiness: IntegrationReadiness = IntegrationReadiness.UNKNOWN
    requires_human_judgement: bool = False
    requires_human_approval: bool = False
    handles_sensitive_data: bool = False
    criticality: Level = Level.UNKNOWN
    problems: list[str] = Field(default_factory=list)


class StepCreate(StepFields):
    position: int | None = Field(
        default=None, ge=1, description="Insert at this position. Appends when omitted."
    )


class StepUpdate(_Schema):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None
    responsible_role: str | None = Field(default=None, max_length=200)
    tools: list[str] | None = None
    input_description: str | None = None
    output_description: str | None = None
    minutes_per_execution: Decimal | None = Field(default=None, ge=0)
    occurrence_rate: Decimal | None = Field(default=None, ge=0, le=1)
    repetitiveness: Level | None = None
    rule_clarity: Level | None = None
    input_type: InputType | None = None
    exception_rate: Decimal | None = Field(default=None, ge=0, le=1)
    integration_readiness: IntegrationReadiness | None = None
    requires_human_judgement: bool | None = None
    requires_human_approval: bool | None = None
    handles_sensitive_data: bool | None = None
    criticality: Level | None = None
    problems: list[str] | None = None


class StepRead(StepFields):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    position: int


class ProcessFields(_Schema):
    name: str = Field(min_length=1, max_length=200)
    description: str = ""
    owner: str | None = Field(default=None, max_length=200)
    executions_per_month: int = Field(ge=0)
    hourly_cost: Decimal | None = Field(
        default=None, ge=0, description="Unknown when omitted. Unknown is not free."
    )


class ProcessCreate(ProcessFields):
    steps: list[StepFields] = Field(default_factory=list)


class ProcessUpdate(_Schema):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None
    owner: str | None = Field(default=None, max_length=200)
    executions_per_month: int | None = Field(default=None, ge=0)
    hourly_cost: Decimal | None = Field(default=None, ge=0)


class ProcessRead(ProcessFields):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    version: int
    created_at: datetime
    updated_at: datetime
    steps: list[StepRead]


class ProcessSummary(_Schema):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    owner: str | None
    executions_per_month: int
    step_count: int
    version: int
    updated_at: datetime


class StepOrder(_Schema):
    step_ids: list[UUID] = Field(description="Every step id of the process, in the new order.")
