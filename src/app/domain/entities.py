"""Process and ProcessStep: the facts a process analysis is built on.

Derived values (monthly hours, cost, scores, ROI) are deliberately absent.
They are computed by ``metrics``, ``scoring`` and ``business_case``.
"""

from dataclasses import dataclass, field
from decimal import Decimal
from uuid import UUID, uuid4

from app.domain.decimals import ONE, ZERO, to_decimal
from app.domain.enums import InputType, IntegrationReadiness, Level
from app.domain.errors import DomainValidationError


@dataclass(frozen=True, slots=True, kw_only=True)
class ProcessStep:
    """One step of a process plus the attributes the scoring rules read.

    Invariants:
      * ``minutes_per_execution >= 0``
      * ``0 <= occurrence_rate <= 1`` (share of executions where the step happens)
      * ``0 <= exception_rate <= 1``, or ``None`` when unknown
      * ``position >= 1``
    """

    name: str
    minutes_per_execution: Decimal
    id: UUID = field(default_factory=uuid4)
    position: int = 1
    description: str = ""
    responsible_role: str = ""
    tools: tuple[str, ...] = ()
    input_description: str = ""
    output_description: str = ""
    occurrence_rate: Decimal = ONE
    repetitiveness: Level = Level.UNKNOWN
    rule_clarity: Level = Level.UNKNOWN
    input_type: InputType = InputType.UNKNOWN
    exception_rate: Decimal | None = None
    integration_readiness: IntegrationReadiness = IntegrationReadiness.UNKNOWN
    requires_human_judgement: bool = False
    requires_human_approval: bool = False
    handles_sensitive_data: bool = False
    criticality: Level = Level.UNKNOWN
    problems: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise DomainValidationError("name", "must not be empty")
        if self.position < 1:
            raise DomainValidationError("position", "must be >= 1")

        minutes = to_decimal(self.minutes_per_execution, "minutes_per_execution")
        if minutes < ZERO:
            raise DomainValidationError("minutes_per_execution", "must be >= 0")
        object.__setattr__(self, "minutes_per_execution", minutes)

        occurrence = to_decimal(self.occurrence_rate, "occurrence_rate")
        _require_unit_interval(occurrence, "occurrence_rate")
        object.__setattr__(self, "occurrence_rate", occurrence)

        if self.exception_rate is not None:
            exceptions = to_decimal(self.exception_rate, "exception_rate")
            _require_unit_interval(exceptions, "exception_rate")
            object.__setattr__(self, "exception_rate", exceptions)

        object.__setattr__(self, "tools", tuple(self.tools))
        object.__setattr__(self, "problems", tuple(self.problems))


@dataclass(frozen=True, slots=True, kw_only=True)
class Process:
    """A business process described as ordered steps.

    Invariants:
      * ``executions_per_month >= 0``
      * ``hourly_cost >= 0``, or ``None`` when unknown (unknown is not free)
      * step positions are unique
    """

    name: str
    executions_per_month: int
    id: UUID = field(default_factory=uuid4)
    description: str = ""
    owner: str | None = None
    hourly_cost: Decimal | None = None
    steps: tuple[ProcessStep, ...] = ()

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise DomainValidationError("name", "must not be empty")
        if isinstance(self.executions_per_month, bool) or not isinstance(
            self.executions_per_month, int
        ):
            raise DomainValidationError("executions_per_month", "must be an integer")
        if self.executions_per_month < 0:
            raise DomainValidationError("executions_per_month", "must be >= 0")

        if self.hourly_cost is not None:
            cost = to_decimal(self.hourly_cost, "hourly_cost")
            if cost < ZERO:
                raise DomainValidationError("hourly_cost", "must be >= 0")
            object.__setattr__(self, "hourly_cost", cost)

        ordered = tuple(sorted(self.steps, key=lambda step: step.position))
        positions = [step.position for step in ordered]
        if len(positions) != len(set(positions)):
            raise DomainValidationError("steps", "step positions must be unique")
        object.__setattr__(self, "steps", ordered)

    def step(self, step_id: UUID) -> ProcessStep:
        for step in self.steps:
            if step.id == step_id:
                return step
        raise KeyError(step_id)


def _require_unit_interval(value: Decimal, field_name: str) -> None:
    if value < ZERO or value > ONE:
        raise DomainValidationError(field_name, "must be between 0 and 1")
