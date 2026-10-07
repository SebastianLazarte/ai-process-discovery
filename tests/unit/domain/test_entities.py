from decimal import Decimal

import pytest

from app.domain.entities import Process, ProcessStep
from app.domain.errors import DomainValidationError
from tests.factories import make_process, make_step


@pytest.mark.parametrize(
    ("overrides", "field"),
    [
        ({"minutes_per_execution": Decimal(-2)}, "minutes_per_execution"),
        ({"occurrence_rate": Decimal("1.2")}, "occurrence_rate"),
        ({"occurrence_rate": Decimal("-0.1")}, "occurrence_rate"),
        ({"exception_rate": Decimal("1.01")}, "exception_rate"),
        ({"exception_rate": Decimal("-0.01")}, "exception_rate"),
        ({"name": "  "}, "name"),
        ({"position": 0}, "position"),
        ({"minutes_per_execution": 2.5}, "minutes_per_execution"),
        ({"minutes_per_execution": "abc"}, "minutes_per_execution"),
        ({"minutes_per_execution": "NaN"}, "minutes_per_execution"),
    ],
)
def test_step_rejects_invalid_values(overrides: dict[str, object], field: str) -> None:
    with pytest.raises(DomainValidationError) as error:
        make_step(**overrides)
    assert error.value.field == field


@pytest.mark.parametrize(
    ("overrides", "field"),
    [
        ({"executions_per_month": -1}, "executions_per_month"),
        ({"executions_per_month": True}, "executions_per_month"),
        ({"hourly_cost": Decimal(-10)}, "hourly_cost"),
        ({"name": ""}, "name"),
    ],
)
def test_process_rejects_invalid_values(overrides: dict[str, object], field: str) -> None:
    with pytest.raises(DomainValidationError) as error:
        make_process(**overrides)
    assert error.value.field == field


def test_process_rejects_duplicate_positions() -> None:
    with pytest.raises(DomainValidationError):
        Process(
            name="P",
            executions_per_month=1,
            steps=(make_step(position=1), make_step(position=1)),
        )


def test_steps_are_kept_in_position_order() -> None:
    second = make_step(name="second", position=2)
    first = make_step(name="first", position=1)
    process = Process(name="P", executions_per_month=1, steps=(second, first))
    assert [s.name for s in process.steps] == ["first", "second"]


def test_ints_and_numeric_strings_become_decimal() -> None:
    step = ProcessStep(name="S", minutes_per_execution=3, occurrence_rate="0.5")  # type: ignore[arg-type]
    assert step.minutes_per_execution == Decimal(3)
    assert step.occurrence_rate == Decimal("0.5")


def test_unknown_exception_rate_is_allowed() -> None:
    assert make_step(exception_rate=None).exception_rate is None


def test_process_lookup_by_step_id() -> None:
    step = make_step()
    process = make_process(step)
    assert process.step(step.id) is step
    with pytest.raises(KeyError):
        process.step(make_step().id)
