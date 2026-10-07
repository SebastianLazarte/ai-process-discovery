"""The minimum M1 cases from the design report, plus the worked invoice example."""

from decimal import Decimal

import pytest

from app.domain.decimals import present_hours, present_money
from app.domain.metrics import (
    calculate_current_state,
    calculate_monthly_cost,
    calculate_process_monthly_hours,
    calculate_step_monthly_hours,
)
from tests.factories import invoice_process, make_process, make_step


def test_empty_process_takes_zero_hours() -> None:
    assert calculate_process_monthly_hours(make_process()) == 0


def test_zero_executions_take_zero_hours() -> None:
    process = make_process(make_step(), executions_per_month=0)
    assert calculate_process_monthly_hours(process) == 0


@pytest.mark.parametrize(
    ("minutes", "occurrence", "expected_hours"),
    [
        (Decimal(6), Decimal(1), Decimal(1)),
        (Decimal(6), Decimal("0.5"), Decimal("0.5")),
        (Decimal(6), Decimal(0), Decimal(0)),
        (Decimal(10), Decimal("0.1"), Decimal(10) / Decimal(60)),
    ],
)
def test_step_hours(minutes: Decimal, occurrence: Decimal, expected_hours: Decimal) -> None:
    step = make_step(minutes_per_execution=minutes, occurrence_rate=occurrence)
    process = make_process(step, executions_per_month=10)
    assert calculate_step_monthly_hours(step, process) == expected_hours


def test_conditional_step_counts_only_when_it_happens() -> None:
    # 100 executions x 10 min x 0.1 occurrence = 100 min/month
    step = make_step(minutes_per_execution=Decimal(10), occurrence_rate=Decimal("0.1"))
    process = make_process(step, executions_per_month=100)
    assert calculate_step_monthly_hours(step, process) * 60 == Decimal(100)


def test_two_steps_add_up() -> None:
    process = make_process(
        make_step(minutes_per_execution=Decimal(6)),
        make_step(minutes_per_execution=Decimal(12)),
        executions_per_month=10,
    )
    assert calculate_process_monthly_hours(process) == Decimal(3)


def test_cost_is_hours_times_hourly_cost() -> None:
    process = make_process(
        make_step(minutes_per_execution=Decimal(60)),
        executions_per_month=10,
        hourly_cost=Decimal(20),
    )
    assert calculate_monthly_cost(process) == Decimal(200)


def test_unknown_hourly_cost_is_none_never_zero() -> None:
    process = make_process(make_step(), hourly_cost=None)
    assert calculate_monthly_cost(process) is None


def test_zero_hourly_cost_is_zero() -> None:
    process = make_process(make_step(), hourly_cost=Decimal(0))
    assert calculate_monthly_cost(process) == Decimal(0)


def test_decimal_precision_is_kept() -> None:
    process = make_process(
        make_step(minutes_per_execution=Decimal("0.1")),
        make_step(minutes_per_execution=Decimal("0.2")),
        executions_per_month=3,
    )
    assert calculate_process_monthly_hours(process) * 60 == Decimal("0.9")


def test_invoice_example_is_not_rounded_early() -> None:
    state = calculate_current_state(invoice_process())
    assert state.monthly_hours == Decimal(1600) / Decimal(60)
    assert present_hours(state.monthly_hours) == Decimal("26.67")
    assert state.monthly_cost is not None
    # The report shows 493.40 because it rounds hours first; 1600 * 18.50 / 60 = 493.33
    assert present_money(state.monthly_cost) == Decimal("493.33")
