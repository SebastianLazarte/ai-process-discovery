"""Deterministic assessment of a whole process: metrics, scores and rule recommendations."""

from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID

from app.domain.classification import (
    HumanControlRecommendation,
    MethodRecommendation,
    classify_method,
    determine_human_control,
)
from app.domain.entities import Process
from app.domain.metrics import CurrentState, calculate_current_state
from app.domain.policies import DEFAULT_POLICY, ScoringPolicy
from app.domain.scoring import StepScore, score_process, score_step


@dataclass(frozen=True, slots=True)
class DeterministicStepAssessment:
    step_id: UUID
    monthly_hours: Decimal
    score: StepScore
    method: MethodRecommendation
    human_control: HumanControlRecommendation


@dataclass(frozen=True, slots=True)
class DeterministicAssessment:
    current_state: CurrentState
    process_score: Decimal | None
    steps: tuple[DeterministicStepAssessment, ...]
    policy_version: str


def assess_process(
    process: Process, policy: ScoringPolicy = DEFAULT_POLICY
) -> DeterministicAssessment:
    current_state = calculate_current_state(process)
    scores = {step.id: score_step(step, process, policy) for step in process.steps}
    steps = tuple(
        DeterministicStepAssessment(
            step_id=step.id,
            monthly_hours=current_state.step_hours[step.id],
            score=scores[step.id],
            method=classify_method(step, policy),
            human_control=determine_human_control(step),
        )
        for step in process.steps
    )
    return DeterministicAssessment(
        current_state=current_state,
        process_score=score_process(process, scores),
        steps=steps,
        policy_version=policy.version,
    )
