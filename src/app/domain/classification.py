"""Rules that recommend an automation method and a level of human control.

Method and human control are separate on purpose: a step can go through an API
and still need a person to approve the result.
"""

from dataclasses import dataclass

from app.domain.entities import ProcessStep
from app.domain.enums import (
    AutomationMethod,
    HumanControl,
    InputType,
    IntegrationReadiness,
    Level,
)
from app.domain.policies import DEFAULT_POLICY, ScoringPolicy


@dataclass(frozen=True, slots=True)
class MethodRecommendation:
    method: AutomationMethod
    reason: str


@dataclass(frozen=True, slots=True)
class HumanControlRecommendation:
    control: HumanControl
    reasons: tuple[str, ...]


def classify_method(
    step: ProcessStep, policy: ScoringPolicy = DEFAULT_POLICY
) -> MethodRecommendation:
    """First matching rule wins. The order is part of the policy and is documented in the spec."""
    if (
        step.rule_clarity is Level.HIGH
        and step.input_type is InputType.DIGITAL_STRUCTURED
        and step.exception_rate is not None
        and step.exception_rate <= policy.rule_based_max_exception_rate
    ):
        return MethodRecommendation(
            AutomationMethod.RULE_BASED,
            "clear rules over structured digital input with few exceptions",
        )
    if step.integration_readiness is IntegrationReadiness.GOOD:
        return MethodRecommendation(
            AutomationMethod.API_INTEGRATION, "the systems involved expose a usable integration"
        )
    if step.input_type is InputType.DIGITAL_UNSTRUCTURED and not step.requires_human_judgement:
        return MethodRecommendation(
            AutomationMethod.AI_CANDIDATE,
            "unstructured digital input without required human judgement",
        )
    if (
        step.input_type is InputType.PHYSICAL
        and step.integration_readiness is IntegrationReadiness.NONE
    ):
        return MethodRecommendation(
            AutomationMethod.MANUAL, "physical input and no integration available"
        )
    return MethodRecommendation(
        AutomationMethod.NEEDS_REVIEW, "no deterministic rule applies; needs analyst review"
    )


def determine_human_control(step: ProcessStep) -> HumanControlRecommendation:
    required: list[str] = []
    if step.requires_human_judgement:
        required.append("requires human judgement")
    if step.requires_human_approval:
        required.append("requires human approval")
    if required:
        return HumanControlRecommendation(HumanControl.REQUIRED, tuple(required))

    recommended: list[str] = []
    if step.handles_sensitive_data:
        recommended.append("handles sensitive data")
    if step.criticality is Level.HIGH:
        recommended.append("high criticality")
    if recommended:
        return HumanControlRecommendation(HumanControl.RECOMMENDED, tuple(recommended))

    return HumanControlRecommendation(HumanControl.NONE, ())
