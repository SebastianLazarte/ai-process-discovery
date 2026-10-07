"""Current-state metrics. Pure functions over ``Process`` with exact Decimal maths.

Formulas:
    step_monthly_minutes = executions_per_month * occurrence_rate * minutes_per_execution
    step_monthly_hours   = step_monthly_minutes / 60
    process_hours        = sum(step_monthly_minutes) / 60
    monthly_cost         = sum(step_monthly_minutes) * hourly_cost / 60   (None if cost unknown)

Division by 60 happens last so no intermediate value is rounded.
"""

from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID

from app.domain.decimals import ZERO
from app.domain.entities import Process, ProcessStep

MINUTES_PER_HOUR = Decimal(60)


@dataclass(frozen=True, slots=True)
class CurrentState:
    monthly_hours: Decimal
    monthly_cost: Decimal | None
    step_hours: dict[UUID, Decimal]


def calculate_step_monthly_minutes(step: ProcessStep, executions_per_month: int) -> Decimal:
    return Decimal(executions_per_month) * step.occurrence_rate * step.minutes_per_execution


def calculate_step_monthly_hours(step: ProcessStep, process: Process) -> Decimal:
    return calculate_step_monthly_minutes(step, process.executions_per_month) / MINUTES_PER_HOUR


def calculate_process_monthly_minutes(process: Process) -> Decimal:
    return sum(
        (calculate_step_monthly_minutes(s, process.executions_per_month) for s in process.steps),
        start=ZERO,
    )


def calculate_process_monthly_hours(process: Process) -> Decimal:
    return calculate_process_monthly_minutes(process) / MINUTES_PER_HOUR


def calculate_monthly_cost(process: Process) -> Decimal | None:
    """Monthly cost of the process. ``None`` when the hourly cost is unknown, never 0."""
    if process.hourly_cost is None:
        return None
    return calculate_process_monthly_minutes(process) * process.hourly_cost / MINUTES_PER_HOUR


def calculate_current_state(process: Process) -> CurrentState:
    return CurrentState(
        monthly_hours=calculate_process_monthly_hours(process),
        monthly_cost=calculate_monthly_cost(process),
        step_hours={step.id: calculate_step_monthly_hours(step, process) for step in process.steps},
    )
