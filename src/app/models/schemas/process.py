"""HTTP contracts for processes and steps. Decimals travel as JSON strings."""

from datetime import datetime
from decimal import Decimal
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.domain.enums import InputType, IntegrationReadiness, Level

# Size limits for a public deployment (RS-60). They bound storage and the prompt sent to
# the LLM provider; the demo processes stay far below them.
MAX_STEPS = 50
MAX_SHORT_TEXT = 200
MAX_LONG_TEXT = 2000
MAX_LIST_ITEMS = 20

ShortText = Annotated[str, Field(max_length=MAX_SHORT_TEXT)]
LongText = Annotated[str, Field(max_length=MAX_LONG_TEXT)]
TextList = Annotated[list[ShortText], Field(max_length=MAX_LIST_ITEMS)]


class _Schema(BaseModel):
    model_config = ConfigDict(extra="forbid")


class StepTraits(_Schema):
    """What a step is, without a single number. Process templates carry only these (RS-95)."""

    name: str = Field(min_length=1, max_length=200)
    description: LongText = ""
    responsible_role: str = Field(default="", max_length=200)
    tools: TextList = Field(default_factory=list)
    input_description: LongText = ""
    output_description: LongText = ""
    repetitiveness: Level = Level.UNKNOWN
    rule_clarity: Level = Level.UNKNOWN
    input_type: InputType = InputType.UNKNOWN
    integration_readiness: IntegrationReadiness = IntegrationReadiness.UNKNOWN
    requires_human_judgement: bool = False
    requires_human_approval: bool = False
    handles_sensitive_data: bool = False
    criticality: Level = Level.UNKNOWN
    problems: TextList = Field(default_factory=list)


class StepFields(StepTraits):
    minutes_per_execution: Decimal = Field(ge=0, examples=["4.0"])
    occurrence_rate: Decimal = Field(default=Decimal(1), ge=0, le=1)
    exception_rate: Decimal | None = Field(default=None, ge=0, le=1)


class StepCreate(StepFields):
    position: int | None = Field(
        default=None, ge=1, description="Insert at this position. Appends when omitted."
    )


class StepUpdate(_Schema):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    description: LongText | None = None
    responsible_role: str | None = Field(default=None, max_length=200)
    tools: TextList | None = None
    input_description: LongText | None = None
    output_description: LongText | None = None
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
    problems: TextList | None = None


class StepRead(StepFields):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    position: int


class ProcessFields(_Schema):
    name: str = Field(min_length=1, max_length=200)
    description: LongText = ""
    owner: str | None = Field(default=None, max_length=200)
    executions_per_month: int = Field(ge=0)
    hourly_cost: Decimal | None = Field(
        default=None, ge=0, description="Unknown when omitted. Unknown is not free."
    )


class ProcessCreate(ProcessFields):
    steps: list[StepFields] = Field(default_factory=list, max_length=MAX_STEPS)


class ProcessUpdate(_Schema):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    description: LongText | None = None
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
    step_ids: list[UUID] = Field(
        max_length=MAX_STEPS, description="Every step id of the process, in the new order."
    )
