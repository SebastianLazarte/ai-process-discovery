"""The rate each plain-word answer stands for (RS-115)."""

from decimal import Decimal

import pytest

from app.domain.enums import ExceptionFrequency, StepFrequency
from app.domain.policies import CAPTURE_POLICY_V1, SCORING_POLICY_V1
from app.domain.scoring import score_step
from tests.factories import make_process, make_step


@pytest.mark.parametrize(
    ("frequency", "rate"),
    [
        (StepFrequency.ALWAYS, Decimal(1)),
        (StepFrequency.MOST_OF_THE_TIME, Decimal("0.75")),
        (StepFrequency.HALF_OF_THE_TIME, Decimal("0.5")),
        (StepFrequency.SOMETIMES, Decimal("0.25")),
        (StepFrequency.RARELY, Decimal("0.1")),
    ],
)
def test_each_frequency_stands_for_one_occurrence_rate(
    frequency: StepFrequency, rate: Decimal
) -> None:
    assert CAPTURE_POLICY_V1.occurrence_rate(frequency) == rate


@pytest.mark.parametrize(
    ("exceptions", "rate", "points"),
    [
        (ExceptionFrequency.ALMOST_NEVER, Decimal("0.02"), 15),
        (ExceptionFrequency.SOMETIMES, Decimal("0.1"), 10),
        (ExceptionFrequency.OFTEN, Decimal("0.33"), 0),
        (ExceptionFrequency.ALMOST_ALWAYS, Decimal("0.8"), 0),
    ],
)
def test_each_exception_answer_lands_in_one_scoring_band(
    exceptions: ExceptionFrequency, rate: Decimal, points: int
) -> None:
    assert CAPTURE_POLICY_V1.exception_rate(exceptions) == rate
    step = make_step(exception_rate=rate)
    score = score_step(step, make_process(step), SCORING_POLICY_V1)
    assert next(f.points for f in score.factors if f.name == "exception_rate") == points


def test_sometimes_still_allows_rules() -> None:
    sometimes = CAPTURE_POLICY_V1.exception_rate(ExceptionFrequency.SOMETIMES)
    assert sometimes == SCORING_POLICY_V1.rule_based_max_exception_rate


def test_dont_know_stays_unknown_and_never_zero() -> None:
    assert CAPTURE_POLICY_V1.exception_rate(ExceptionFrequency.UNKNOWN) is None


def test_every_answer_has_a_rate_within_zero_and_one() -> None:
    occurrences = [CAPTURE_POLICY_V1.occurrence_rate(f) for f in StepFrequency]
    exceptions = [CAPTURE_POLICY_V1.exception_rate(e) for e in ExceptionFrequency]
    assert all(Decimal(0) < rate <= 1 for rate in occurrences)
    assert all(rate is None or Decimal(0) < rate < 1 for rate in exceptions)
