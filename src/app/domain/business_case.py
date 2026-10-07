"""Business impact: hours freed, savings, payback and ROI.

Every economic input is a user assumption. The system never estimates the
implementation cost or the time reduction, and the LLM never sees these values.
"""

from collections.abc import Mapping
from dataclasses import dataclass, field
from decimal import Decimal
from types import MappingProxyType
from uuid import UUID

from app.domain.decimals import ONE, ZERO, to_decimal
from app.domain.entities import Process
from app.domain.errors import DomainValidationError
from app.domain.metrics import MINUTES_PER_HOUR, calculate_step_monthly_minutes

MONTHS_PER_YEAR = Decimal(12)


@dataclass(frozen=True, slots=True, kw_only=True)
class BusinessCaseAssumptions:
    """User-supplied scenario. Kept apart from ``Process`` so scenarios can vary freely."""

    implementation_cost: Decimal | None = None
    monthly_tooling_cost: Decimal = ZERO
    expected_time_reduction_by_step: Mapping[UUID, Decimal] = field(
        default_factory=lambda: MappingProxyType({})
    )

    def __post_init__(self) -> None:
        if self.implementation_cost is not None:
            cost = to_decimal(self.implementation_cost, "implementation_cost")
            if cost < ZERO:
                raise DomainValidationError("implementation_cost", "must be >= 0")
            object.__setattr__(self, "implementation_cost", cost)

        tooling = to_decimal(self.monthly_tooling_cost, "monthly_tooling_cost")
        if tooling < ZERO:
            raise DomainValidationError("monthly_tooling_cost", "must be >= 0")
        object.__setattr__(self, "monthly_tooling_cost", tooling)

        reductions: dict[UUID, Decimal] = {}
        for step_id, raw in self.expected_time_reduction_by_step.items():
            value = to_decimal(raw, "expected_time_reduction_by_step")
            if value < ZERO or value > ONE:
                raise DomainValidationError(
                    "expected_time_reduction_by_step", f"{step_id}: must be between 0 and 1"
                )
            reductions[step_id] = value
        object.__setattr__(self, "expected_time_reduction_by_step", MappingProxyType(reductions))


@dataclass(frozen=True, slots=True)
class BusinessCase:
    current_monthly_hours: Decimal
    estimated_hours_saved: Decimal
    hours_saved_by_step: dict[UUID, Decimal]
    estimated_monthly_savings: Decimal | None
    monthly_tooling_cost: Decimal
    net_monthly_savings: Decimal | None
    implementation_cost: Decimal | None
    payback_months: Decimal | None
    roi_12_months: Decimal | None
    steps_without_reduction: tuple[UUID, ...]


def calculate_business_case(process: Process, assumptions: BusinessCaseAssumptions) -> BusinessCase:
    step_ids = {step.id for step in process.steps}
    unknown = set(assumptions.expected_time_reduction_by_step) - step_ids
    if unknown:
        raise DomainValidationError(
            "expected_time_reduction_by_step",
            f"unknown step ids: {', '.join(sorted(str(s) for s in unknown))}",
        )

    total_minutes = ZERO
    saved_minutes_by_step: dict[UUID, Decimal] = {}
    without_reduction: list[UUID] = []
    for step in process.steps:
        minutes = calculate_step_monthly_minutes(step, process.executions_per_month)
        total_minutes += minutes
        reduction = assumptions.expected_time_reduction_by_step.get(step.id)
        if reduction is None:
            # A missing assumption counts as no saving and is reported as missing.
            without_reduction.append(step.id)
            reduction = ZERO
        saved_minutes_by_step[step.id] = minutes * reduction

    saved_minutes = sum(saved_minutes_by_step.values(), start=ZERO)
    hours_saved = saved_minutes / MINUTES_PER_HOUR

    gross: Decimal | None = None
    net: Decimal | None = None
    if process.hourly_cost is not None:
        gross = saved_minutes * process.hourly_cost / MINUTES_PER_HOUR
        net = gross - assumptions.monthly_tooling_cost

    implementation = assumptions.implementation_cost
    payback: Decimal | None = None
    roi: Decimal | None = None
    if net is not None and implementation is not None:
        if net > ZERO:
            payback = implementation / net
        if implementation > ZERO:
            roi = (net * MONTHS_PER_YEAR - implementation) / implementation

    return BusinessCase(
        current_monthly_hours=total_minutes / MINUTES_PER_HOUR,
        estimated_hours_saved=hours_saved,
        hours_saved_by_step={k: v / MINUTES_PER_HOUR for k, v in saved_minutes_by_step.items()},
        estimated_monthly_savings=gross,
        monthly_tooling_cost=assumptions.monthly_tooling_cost,
        net_monthly_savings=net,
        implementation_cost=implementation,
        payback_months=payback,
        roi_12_months=roi,
        steps_without_reduction=tuple(without_reduction),
    )
