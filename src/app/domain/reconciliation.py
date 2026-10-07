"""Reconciliation of deterministic rules with an AI suggestion.

Authority order: hard constraints > deterministic rules > AI suggestion > human override.
The AI may add safeguards. It can never remove one.
"""

from dataclasses import dataclass
from enum import StrEnum

from app.domain.assessment import DeterministicStepAssessment
from app.domain.enums import AutomationMethod, HumanControl


class RecommendationSource(StrEnum):
    RULES = "RULES"
    AI = "AI"
    HUMAN = "HUMAN"


@dataclass(frozen=True, slots=True, kw_only=True)
class AISuggestion:
    """Provider-neutral view of what the model suggested for one step."""

    method: AutomationMethod
    confidence: float
    interpretation: str
    rationale: str
    human_control_recommended: bool
    dependencies: tuple[str, ...] = ()
    risks: tuple[str, ...] = ()
    uncertainties: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class FinalRecommendation:
    method: AutomationMethod
    human_control: HumanControl
    source: RecommendationSource
    notes: tuple[str, ...]


def reconcile(rules: DeterministicStepAssessment, ai: AISuggestion | None) -> FinalRecommendation:
    rules_method = rules.method.method
    rules_control = rules.human_control.control

    if ai is None:
        return FinalRecommendation(rules_method, rules_control, RecommendationSource.RULES, ())

    notes: list[str] = []

    # Human control: the AI can raise it to RECOMMENDED, never lower it.
    ai_control = HumanControl.RECOMMENDED if ai.human_control_recommended else HumanControl.NONE
    control = HumanControl.strongest(rules_control, ai_control)
    if control is not rules_control:
        notes.append(f"AI raised human control from {rules_control} to {control}")
    elif not ai.human_control_recommended and rules_control is not HumanControl.NONE:
        notes.append(f"AI suggested no human control; kept {rules_control} from rules")

    # Method: the AI only decides where the rules could not.
    if rules_method is AutomationMethod.NEEDS_REVIEW:
        return FinalRecommendation(ai.method, control, RecommendationSource.AI, tuple(notes))

    if ai.method is not rules_method:
        notes.append(f"AI suggested {ai.method}; kept {rules_method} from rules")
    source = RecommendationSource.AI if control is not rules_control else RecommendationSource.RULES
    return FinalRecommendation(rules_method, control, source, tuple(notes))
