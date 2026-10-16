"""Properties the domain keeps for every valid input, checked with generated examples.

Example tests prove a rule on the cases someone thought of. These prove the hard rules
(``CLAUDE.md``) on hundreds of generated processes, steps and AI suggestions.
"""

from collections.abc import Callable
from decimal import Decimal

import pytest
from hypothesis import given
from hypothesis import strategies as st

from app.domain.assessment import assess_process
from app.domain.business_case import BusinessCaseAssumptions, calculate_business_case
from app.domain.decimals import ZERO, present_hours, present_money, present_ratio
from app.domain.entities import Process, ProcessStep
from app.domain.enums import AutomationMethod, HumanControl, Level
from app.domain.errors import DomainValidationError
from app.domain.metrics import MINUTES_PER_HOUR, calculate_step_monthly_minutes
from app.domain.reconciliation import AISuggestion, RecommendationSource, reconcile
from tests.factories import make_process, make_step
from tests.strategies import ai_suggestions, money, processes, steps, unit_interval

# Hard rule 3: the LLM may raise a human control and never lower it.


@given(step=steps(), ai=ai_suggestions)
def test_ai_never_lowers_human_control(step: ProcessStep, ai: AISuggestion) -> None:
    (rules,) = assess_process(make_process(step)).steps
    final = reconcile(rules, ai)
    assert final.human_control.rank >= rules.human_control.control.rank
    if ai.human_control_recommended:
        assert final.human_control.rank >= HumanControl.RECOMMENDED.rank


@given(step=steps(), ai=ai_suggestions)
def test_ai_decides_the_method_only_where_rules_need_review(
    step: ProcessStep, ai: AISuggestion
) -> None:
    (rules,) = assess_process(make_process(step)).steps
    final = reconcile(rules, ai)
    if rules.method.method is AutomationMethod.NEEDS_REVIEW:
        assert final.method is ai.method
        assert final.source is RecommendationSource.AI
    else:
        assert final.method is rules.method.method


@given(step=steps(), ai=ai_suggestions)
def test_source_is_ai_only_when_the_ai_changed_something(
    step: ProcessStep, ai: AISuggestion
) -> None:
    (rules,) = assess_process(make_process(step)).steps
    final = reconcile(rules, ai)
    changed = (
        final.method is not rules.method.method
        or final.human_control is not rules.human_control.control
        or rules.method.method is AutomationMethod.NEEDS_REVIEW
    )
    assert (final.source is RecommendationSource.AI) is changed


@given(step=steps())
def test_without_ai_the_rules_decide_with_no_notes(step: ProcessStep) -> None:
    (rules,) = assess_process(make_process(step)).steps
    final = reconcile(rules, None)
    assert (final.method, final.human_control) == (
        rules.method.method,
        rules.human_control.control,
    )
    assert final.notes == ()


@given(controls=st.lists(st.sampled_from(HumanControl), min_size=1))
def test_strongest_control_has_the_highest_rank(controls: list[HumanControl]) -> None:
    strongest = HumanControl.strongest(*controls)
    assert strongest in controls
    assert all(strongest.rank >= control.rank for control in controls)


# Business case: totals add up and stay within their bounds.


def _hours(process: Process) -> Decimal:
    return (
        sum(
            (
                calculate_step_monthly_minutes(s, process.executions_per_month)
                for s in process.steps
            ),
            start=ZERO,
        )
        / MINUTES_PER_HOUR
    )


@given(process=processes(), data=st.data())
def test_hours_saved_never_exceed_current_hours(process: Process, data: st.DataObject) -> None:
    reductions = {
        step.id: data.draw(unit_interval) for step in process.steps if data.draw(st.booleans())
    }
    case = calculate_business_case(
        process, BusinessCaseAssumptions(expected_time_reduction_by_step=reductions)
    )
    assert case.current_monthly_hours == _hours(process)
    assert ZERO <= case.estimated_hours_saved <= case.current_monthly_hours
    # Division by 60 keeps 28 significant digits, so the parts add up to that precision.
    parts = sum(case.hours_saved_by_step.values(), start=ZERO)
    assert abs(parts - case.estimated_hours_saved) <= Decimal("1e-20")
    assert set(case.steps_without_reduction) == {
        s.id for s in process.steps if s.id not in reductions
    }


@given(process=processes(), tooling=money, implementation=st.none() | money)
def test_net_savings_payback_and_roi_are_consistent(
    process: Process, tooling: Decimal, implementation: Decimal | None
) -> None:
    full = {step.id: Decimal(1) for step in process.steps}
    case = calculate_business_case(
        process,
        BusinessCaseAssumptions(
            implementation_cost=implementation,
            monthly_tooling_cost=tooling,
            expected_time_reduction_by_step=full,
        ),
    )
    assert case.monthly_tooling_cost == tooling
    assert case.implementation_cost == implementation
    if process.hourly_cost is None:
        assert case.estimated_monthly_savings is None
        assert case.net_monthly_savings is None
        assert case.payback_months is None
        return
    assert case.net_monthly_savings == case.estimated_monthly_savings - tooling
    net = case.net_monthly_savings
    if implementation is None or net <= ZERO:
        assert case.payback_months is None
    else:
        assert case.payback_months == implementation / net


def test_payback_is_unknown_when_net_savings_are_exactly_zero() -> None:
    step = make_step(minutes_per_execution=Decimal(60))
    process = make_process(step, executions_per_month=1, hourly_cost=Decimal(10))
    case = calculate_business_case(
        process,
        BusinessCaseAssumptions(
            implementation_cost=Decimal(100),
            monthly_tooling_cost=Decimal(10),
            expected_time_reduction_by_step={step.id: Decimal(1)},
        ),
    )
    assert case.net_monthly_savings == ZERO
    assert case.payback_months is None


# Hard rule 4: rounding happens only on presentation, half up, to the stated precision.


@pytest.mark.parametrize("present", [present_money, present_hours, present_ratio])
@pytest.mark.parametrize(
    ("raw", "shown"),
    [("0.125", "0.13"), ("0.005", "0.01"), ("2.675", "2.68"), ("-0.125", "-0.13")],
)
def test_presentation_rounds_ties_half_up(present: object, raw: str, shown: str) -> None:
    assert present(Decimal(raw)) == Decimal(shown)  # type: ignore[operator]


@given(value=st.decimals(allow_nan=False, allow_infinity=False, min_value=-1e9, max_value=1e9))
def test_presented_money_is_within_half_a_cent(value: Decimal) -> None:
    shown = present_money(value)
    assert shown.as_tuple().exponent == -2
    assert abs(shown - value) <= Decimal("0.005")


def test_ai_agreeing_on_no_control_adds_no_note() -> None:
    (rules,) = assess_process(make_process(make_step(criticality=Level.LOW))).steps
    assert rules.human_control.control is HumanControl.NONE
    ai = AISuggestion(
        method=rules.method.method,
        confidence=0.9,
        interpretation="i",
        rationale="r",
        human_control_recommended=False,
    )
    assert reconcile(rules, ai).notes == ()


# Validation names the offending field, which the API returns to the client.


@pytest.mark.parametrize(
    ("build", "field"),
    [
        (lambda: make_step(position=0), "position"),
        (lambda: make_step(minutes_per_execution=-1), "minutes_per_execution"),
        (lambda: make_step(minutes_per_execution="abc"), "minutes_per_execution"),
        (lambda: make_step(occurrence_rate=2), "occurrence_rate"),
        (lambda: make_step(occurrence_rate="x"), "occurrence_rate"),
        (lambda: make_step(exception_rate=-1), "exception_rate"),
        (lambda: make_step(exception_rate="x"), "exception_rate"),
        (lambda: make_process(executions_per_month=-1), "executions_per_month"),
        (lambda: make_process(hourly_cost=-1), "hourly_cost"),
        (lambda: make_process(hourly_cost="x"), "hourly_cost"),
        (
            lambda: Process(name="P", executions_per_month=1, steps=(make_step(), make_step())),
            "steps",
        ),
        (lambda: BusinessCaseAssumptions(implementation_cost=-1), "implementation_cost"),
        (lambda: BusinessCaseAssumptions(implementation_cost="x"), "implementation_cost"),
        (lambda: BusinessCaseAssumptions(monthly_tooling_cost=-1), "monthly_tooling_cost"),
        (lambda: BusinessCaseAssumptions(monthly_tooling_cost="x"), "monthly_tooling_cost"),
    ],
)
def test_invalid_input_reports_its_field(build: Callable[[], object], field: str) -> None:
    with pytest.raises(DomainValidationError) as error:
        build()
    assert error.value.field == field
