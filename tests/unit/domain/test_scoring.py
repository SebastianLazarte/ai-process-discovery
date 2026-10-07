from dataclasses import replace
from decimal import Decimal

import pytest

from app.domain.enums import InputType, IntegrationReadiness, Level
from app.domain.policies import SCORING_POLICY_V1
from app.domain.scoring import StepScore, score_process, score_step
from tests.factories import make_process, make_step


def _factor(score: StepScore, name: str) -> int:
    return next(f.points for f in score.factors if f.name == name)


@pytest.mark.parametrize(
    ("executions", "occurrence", "points"),
    [
        (0, Decimal(1), 2),
        (4, Decimal(1), 2),
        (5, Decimal(1), 6),
        (19, Decimal(1), 6),
        (20, Decimal(1), 10),
        (50, Decimal(1), 15),
        (199, Decimal(1), 15),
        (200, Decimal(1), 20),
        (400, Decimal("0.1"), 10),  # frequency uses effective executions
    ],
)
def test_frequency_bands(executions: int, occurrence: Decimal, points: int) -> None:
    step = make_step(occurrence_rate=occurrence)
    process = make_process(step, executions_per_month=executions)
    assert _factor(score_step(step, process), "frequency") == points


@pytest.mark.parametrize(
    ("rate", "points"),
    [
        (Decimal(0), 15),
        (Decimal("0.05"), 15),
        (Decimal("0.06"), 10),
        (Decimal("0.15"), 10),
        (Decimal("0.30"), 5),
        (Decimal("0.31"), 0),
        (None, 0),
    ],
)
def test_exception_bands(rate: Decimal | None, points: int) -> None:
    step = make_step(exception_rate=rate)
    assert _factor(score_step(step, make_process(step)), "exception_rate") == points


def test_perfect_step_scores_100() -> None:
    step = make_step(
        repetitiveness=Level.HIGH,
        rule_clarity=Level.HIGH,
        input_type=InputType.DIGITAL_STRUCTURED,
        exception_rate=Decimal(0),
        integration_readiness=IntegrationReadiness.GOOD,
        criticality=Level.LOW,
    )
    result = score_step(step, make_process(step, executions_per_month=500))
    assert result.score == 100
    assert result.penalties == ()
    assert result.unknowns == ()
    assert result.policy_version == "scoring-v1"


def test_score_equals_factors_minus_penalties_clamped() -> None:
    step = make_step(handles_sensitive_data=True, criticality=Level.HIGH)
    result = score_step(step, make_process(step, executions_per_month=500))
    raw = sum(f.points for f in result.factors) - sum(p.points for p in result.penalties)
    assert result.score == max(0, min(100, raw))
    assert {p.name for p in result.penalties} == {"sensitive_data", "high_criticality"}


def test_score_never_goes_below_zero() -> None:
    step = make_step(
        repetitiveness=Level.LOW,
        rule_clarity=Level.LOW,
        input_type=InputType.PHYSICAL,
        exception_rate=Decimal("0.9"),
        integration_readiness=IntegrationReadiness.NONE,
        requires_human_judgement=True,
        handles_sensitive_data=True,
        criticality=Level.HIGH,
    )
    assert score_step(step, make_process(step, executions_per_month=1)).score == 0


def test_unknown_attributes_score_zero_and_are_listed() -> None:
    step = make_step(
        repetitiveness=Level.UNKNOWN,
        rule_clarity=Level.UNKNOWN,
        input_type=InputType.UNKNOWN,
        exception_rate=None,
        integration_readiness=IntegrationReadiness.UNKNOWN,
        criticality=Level.UNKNOWN,
    )
    result = score_step(step, make_process(step))
    assert set(result.unknowns) == {
        "repetitiveness",
        "rule_clarity",
        "input_type",
        "exception_rate",
        "integration_readiness",
        "criticality",
    }
    assert result.score == _factor(result, "frequency")


def test_policy_weights_change_the_score_without_touching_the_algorithm() -> None:
    step = make_step(handles_sensitive_data=True)
    process = make_process(step)
    lenient = replace(SCORING_POLICY_V1, version="test", sensitive_data_penalty=0)
    base = score_step(step, process)
    changed = score_step(step, process, lenient)
    assert changed.score == base.score + SCORING_POLICY_V1.sensitive_data_penalty
    assert changed.policy_version == "test"


def test_process_score_is_weighted_by_time() -> None:
    # 1 h at score 90 and 9 h at score 50 -> (90 + 450) / 10 = 54
    short = make_step(minutes_per_execution=Decimal(6))
    long = make_step(minutes_per_execution=Decimal(54))
    process = make_process(short, long, executions_per_month=10)
    scores = {
        short.id: StepScore(short.id, 90, (), (), (), "v"),
        long.id: StepScore(long.id, 50, (), (), (), "v"),
    }
    assert score_process(process, scores) == Decimal(54)


def test_process_score_is_none_without_time() -> None:
    step = make_step()
    process = make_process(step, executions_per_month=0)
    assert score_process(process, {step.id: score_step(step, process)}) is None


def test_max_points_add_up_to_100() -> None:
    assert sum(SCORING_POLICY_V1.max_points.values()) == 100
