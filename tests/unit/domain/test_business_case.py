from decimal import Decimal
from uuid import uuid4

import pytest

from app.domain.business_case import BusinessCaseAssumptions, calculate_business_case
from app.domain.errors import DomainValidationError
from tests.factories import make_process, make_step


def _ten_hour_process(hourly_cost: Decimal | None = Decimal(20)):  # type: ignore[no-untyped-def]
    step = make_step(minutes_per_execution=Decimal(60))
    return step, make_process(step, executions_per_month=10, hourly_cost=hourly_cost)


def test_hours_saved_apply_the_expected_reduction() -> None:
    step, process = _ten_hour_process()
    case = calculate_business_case(
        process, BusinessCaseAssumptions(expected_time_reduction_by_step={step.id: Decimal("0.5")})
    )
    assert case.current_monthly_hours == Decimal(10)
    assert case.estimated_hours_saved == Decimal(5)
    assert case.hours_saved_by_step == {step.id: Decimal(5)}
    assert case.steps_without_reduction == ()


def test_savings_payback_and_roi() -> None:
    step, process = _ten_hour_process()
    case = calculate_business_case(
        process,
        BusinessCaseAssumptions(
            implementation_cost=Decimal(1000),
            monthly_tooling_cost=Decimal(20),
            expected_time_reduction_by_step={step.id: Decimal("0.5")},
        ),
    )
    assert case.estimated_monthly_savings == Decimal(100)
    assert case.net_monthly_savings == Decimal(80)
    assert case.payback_months == Decimal("12.5")
    assert case.roi_12_months == Decimal("-0.04")


def test_unknown_hourly_cost_leaves_money_unknown() -> None:
    step, process = _ten_hour_process(hourly_cost=None)
    case = calculate_business_case(
        process,
        BusinessCaseAssumptions(
            implementation_cost=Decimal(1000),
            expected_time_reduction_by_step={step.id: Decimal(1)},
        ),
    )
    assert case.estimated_hours_saved == Decimal(10)
    assert case.estimated_monthly_savings is None
    assert case.net_monthly_savings is None
    assert case.payback_months is None
    assert case.roi_12_months is None


def test_no_payback_when_net_savings_are_not_positive() -> None:
    step, process = _ten_hour_process()
    case = calculate_business_case(
        process,
        BusinessCaseAssumptions(
            implementation_cost=Decimal(1000),
            monthly_tooling_cost=Decimal(500),
            expected_time_reduction_by_step={step.id: Decimal("0.5")},
        ),
    )
    assert case.net_monthly_savings == Decimal(-400)
    assert case.payback_months is None


def test_free_implementation_pays_back_immediately_without_roi() -> None:
    step, process = _ten_hour_process()
    case = calculate_business_case(
        process,
        BusinessCaseAssumptions(
            implementation_cost=Decimal(0),
            expected_time_reduction_by_step={step.id: Decimal("0.5")},
        ),
    )
    assert case.payback_months == Decimal(0)
    assert case.roi_12_months is None


def test_missing_reduction_counts_as_zero_and_is_reported() -> None:
    step, process = _ten_hour_process()
    case = calculate_business_case(process, BusinessCaseAssumptions())
    assert case.estimated_hours_saved == Decimal(0)
    assert case.steps_without_reduction == (step.id,)
    assert case.implementation_cost is None
    assert case.payback_months is None


@pytest.mark.parametrize(
    "kwargs",
    [
        {"implementation_cost": Decimal(-1)},
        {"monthly_tooling_cost": Decimal(-1)},
        {"expected_time_reduction_by_step": {uuid4(): Decimal("1.5")}},
    ],
)
def test_invalid_assumptions_are_rejected(kwargs: dict[str, object]) -> None:
    with pytest.raises(DomainValidationError):
        BusinessCaseAssumptions(**kwargs)  # type: ignore[arg-type]


def test_reduction_for_unknown_step_is_rejected() -> None:
    _, process = _ten_hour_process()
    with pytest.raises(DomainValidationError):
        calculate_business_case(
            process,
            BusinessCaseAssumptions(expected_time_reduction_by_step={uuid4(): Decimal("0.5")}),
        )
