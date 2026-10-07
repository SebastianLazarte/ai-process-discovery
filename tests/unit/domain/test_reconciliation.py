from decimal import Decimal

from app.domain.assessment import DeterministicStepAssessment, assess_process
from app.domain.enums import AutomationMethod, HumanControl, InputType, IntegrationReadiness, Level
from app.domain.reconciliation import AISuggestion, RecommendationSource, reconcile
from tests.factories import make_process, make_step


def _rules_for(**overrides: object) -> DeterministicStepAssessment:
    step = make_step(**overrides)
    (assessment,) = assess_process(make_process(step)).steps
    return assessment


def _ai(method: AutomationMethod, human_control: bool) -> AISuggestion:
    return AISuggestion(
        method=method,
        confidence=0.8,
        interpretation="i",
        rationale="r",
        human_control_recommended=human_control,
    )


def test_without_ai_the_rules_decide() -> None:
    rules = _rules_for()
    final = reconcile(rules, None)
    assert final.method is rules.method.method
    assert final.human_control is rules.human_control.control
    assert final.source is RecommendationSource.RULES


def test_ai_cannot_remove_a_required_control() -> None:
    rules = _rules_for(requires_human_approval=True)
    assert rules.human_control.control is HumanControl.REQUIRED
    final = reconcile(rules, _ai(rules.method.method, human_control=False))
    assert final.human_control is HumanControl.REQUIRED
    assert any("kept REQUIRED" in note for note in final.notes)


def test_ai_cannot_remove_a_recommended_control() -> None:
    rules = _rules_for(handles_sensitive_data=True)
    final = reconcile(rules, _ai(rules.method.method, human_control=False))
    assert final.human_control is HumanControl.RECOMMENDED


def test_ai_can_raise_human_control() -> None:
    rules = _rules_for()
    assert rules.human_control.control is HumanControl.NONE
    final = reconcile(rules, _ai(rules.method.method, human_control=True))
    assert final.human_control is HumanControl.RECOMMENDED
    assert final.source is RecommendationSource.AI


def test_ai_decides_the_method_only_when_rules_need_review() -> None:
    rules = _rules_for(input_type=InputType.MIXED, integration_readiness=IntegrationReadiness.NONE)
    assert rules.method.method is AutomationMethod.NEEDS_REVIEW
    final = reconcile(rules, _ai(AutomationMethod.HYBRID, human_control=False))
    assert final.method is AutomationMethod.HYBRID
    assert final.source is RecommendationSource.AI


def test_clear_rule_beats_ai_method() -> None:
    rules = _rules_for(
        rule_clarity=Level.HIGH,
        input_type=InputType.DIGITAL_STRUCTURED,
        exception_rate=Decimal("0.01"),
    )
    assert rules.method.method is AutomationMethod.RULE_BASED
    final = reconcile(rules, _ai(AutomationMethod.AI_CANDIDATE, human_control=False))
    assert final.method is AutomationMethod.RULE_BASED
    assert final.source is RecommendationSource.RULES
    assert any("kept RULE_BASED" in note for note in final.notes)
