"""Automation suitability scoring.

Suitability answers "does it make technical sense to automate this step?".
It is never mixed with business impact (see ``business_case.py``).
"""

from collections.abc import Mapping
from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID

from app.domain.decimals import ZERO
from app.domain.entities import Process, ProcessStep
from app.domain.enums import InputType, IntegrationReadiness, Level
from app.domain.metrics import calculate_step_monthly_minutes
from app.domain.policies import DEFAULT_POLICY, ScoringPolicy


@dataclass(frozen=True, slots=True)
class ScoreFactor:
    name: str
    points: int
    max_points: int
    detail: str


@dataclass(frozen=True, slots=True)
class ScorePenalty:
    name: str
    points: int


@dataclass(frozen=True, slots=True)
class StepScore:
    step_id: UUID
    score: int
    factors: tuple[ScoreFactor, ...]
    penalties: tuple[ScorePenalty, ...]
    unknowns: tuple[str, ...]
    policy_version: str


def score_step(
    step: ProcessStep, process: Process, policy: ScoringPolicy = DEFAULT_POLICY
) -> StepScore:
    maxima = policy.max_points
    factors: list[ScoreFactor] = []
    unknowns: list[str] = []

    effective_executions = Decimal(process.executions_per_month) * step.occurrence_rate
    factors.append(
        ScoreFactor(
            "frequency",
            _floor_points(effective_executions, policy),
            maxima["frequency"],
            f"{effective_executions.normalize():f} effective executions/month",
        )
    )

    factors.append(
        _level_factor(
            "repetitiveness", step.repetitiveness, policy.repetitiveness_points, maxima, unknowns
        )
    )
    factors.append(
        _level_factor(
            "rule_clarity", step.rule_clarity, policy.rule_clarity_points, maxima, unknowns
        )
    )

    if step.input_type is InputType.UNKNOWN:
        unknowns.append("input_type")
    factors.append(
        ScoreFactor(
            "input_type",
            policy.input_type_points[step.input_type],
            maxima["input_type"],
            step.input_type.value,
        )
    )

    if step.exception_rate is None:
        unknowns.append("exception_rate")
        factors.append(ScoreFactor("exception_rate", 0, maxima["exception_rate"], "unknown"))
    else:
        factors.append(
            ScoreFactor(
                "exception_rate",
                _ceiling_points(step.exception_rate, policy),
                maxima["exception_rate"],
                f"{step.exception_rate.normalize():f} of executions",
            )
        )

    if step.integration_readiness is IntegrationReadiness.UNKNOWN:
        unknowns.append("integration_readiness")
    factors.append(
        ScoreFactor(
            "integration_readiness",
            policy.integration_points[step.integration_readiness],
            maxima["integration_readiness"],
            step.integration_readiness.value,
        )
    )

    penalties: list[ScorePenalty] = []
    if step.requires_human_judgement:
        penalties.append(ScorePenalty("human_judgement", policy.human_judgement_penalty))
    if step.handles_sensitive_data:
        penalties.append(ScorePenalty("sensitive_data", policy.sensitive_data_penalty))
    if step.criticality is Level.HIGH:
        penalties.append(ScorePenalty("high_criticality", policy.high_criticality_penalty))
    if step.criticality is Level.UNKNOWN:
        unknowns.append("criticality")

    raw = sum(f.points for f in factors) - sum(p.points for p in penalties)
    return StepScore(
        step_id=step.id,
        score=max(0, min(100, raw)),
        factors=tuple(factors),
        penalties=tuple(penalties),
        unknowns=tuple(unknowns),
        policy_version=policy.version,
    )


def score_process(process: Process, step_scores: dict[UUID, StepScore]) -> Decimal | None:
    """Time-weighted mean of step scores.

    A step that takes 70 % of the monthly time weighs 70 %. Returns ``None`` when the
    process consumes no time, because there is nothing to weigh.
    """
    weighted = ZERO
    total_minutes = ZERO
    for step in process.steps:
        minutes = calculate_step_monthly_minutes(step, process.executions_per_month)
        weighted += Decimal(step_scores[step.id].score) * minutes
        total_minutes += minutes
    if total_minutes == ZERO:
        return None
    return weighted / total_minutes


def _floor_points(value: Decimal, policy: ScoringPolicy) -> int:
    for band in policy.frequency_floors:
        if value >= band.threshold:
            return band.points
    return 0


def _ceiling_points(value: Decimal, policy: ScoringPolicy) -> int:
    for band in policy.exception_ceilings:
        if value <= band.threshold:
            return band.points
    return 0


def _level_factor(
    name: str,
    level: Level,
    table: Mapping[Level, int],
    maxima: dict[str, int],
    unknowns: list[str],
) -> ScoreFactor:
    if level is Level.UNKNOWN:
        unknowns.append(name)
    return ScoreFactor(name, table[level], maxima[name], level.value)
