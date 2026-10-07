from decimal import Decimal

import pytest

from app.domain.assessment import assess_process
from app.domain.classification import classify_method, determine_human_control
from app.domain.enums import AutomationMethod, HumanControl, InputType, IntegrationReadiness, Level
from tests.factories import invoice_process, make_step


@pytest.mark.parametrize(
    ("overrides", "expected"),
    [
        (
            {
                "rule_clarity": Level.HIGH,
                "input_type": InputType.DIGITAL_STRUCTURED,
                "exception_rate": Decimal("0.10"),
            },
            AutomationMethod.RULE_BASED,
        ),
        (
            {
                "rule_clarity": Level.HIGH,
                "input_type": InputType.DIGITAL_STRUCTURED,
                "exception_rate": None,
                "integration_readiness": IntegrationReadiness.GOOD,
            },
            AutomationMethod.API_INTEGRATION,
        ),
        (
            {
                "rule_clarity": Level.HIGH,
                "input_type": InputType.DIGITAL_STRUCTURED,
                "exception_rate": Decimal("0.11"),
                "integration_readiness": IntegrationReadiness.PARTIAL,
            },
            AutomationMethod.NEEDS_REVIEW,
        ),
        (
            {
                "input_type": InputType.DIGITAL_UNSTRUCTURED,
                "integration_readiness": IntegrationReadiness.NONE,
            },
            AutomationMethod.AI_CANDIDATE,
        ),
        (
            {
                "input_type": InputType.DIGITAL_UNSTRUCTURED,
                "integration_readiness": IntegrationReadiness.NONE,
                "requires_human_judgement": True,
            },
            AutomationMethod.NEEDS_REVIEW,
        ),
        (
            {"input_type": InputType.PHYSICAL, "integration_readiness": IntegrationReadiness.NONE},
            AutomationMethod.MANUAL,
        ),
        (
            {"input_type": InputType.MIXED, "integration_readiness": IntegrationReadiness.UNKNOWN},
            AutomationMethod.NEEDS_REVIEW,
        ),
    ],
)
def test_method_rules(overrides: dict[str, object], expected: AutomationMethod) -> None:
    assert classify_method(make_step(**overrides)).method is expected


@pytest.mark.parametrize(
    ("overrides", "expected"),
    [
        ({}, HumanControl.NONE),
        ({"handles_sensitive_data": True}, HumanControl.RECOMMENDED),
        ({"criticality": Level.HIGH}, HumanControl.RECOMMENDED),
        ({"requires_human_judgement": True}, HumanControl.REQUIRED),
        ({"requires_human_approval": True, "handles_sensitive_data": True}, HumanControl.REQUIRED),
    ],
)
def test_human_control_rules(overrides: dict[str, object], expected: HumanControl) -> None:
    result = determine_human_control(make_step(**overrides))
    assert result.control is expected
    assert bool(result.reasons) is (expected is not HumanControl.NONE)


def test_human_control_ordering() -> None:
    assert HumanControl.strongest(HumanControl.NONE, HumanControl.REQUIRED) is HumanControl.REQUIRED
    assert (
        HumanControl.strongest(HumanControl.RECOMMENDED, HumanControl.NONE)
        is HumanControl.RECOMMENDED
    )


def test_assess_invoice_process() -> None:
    process = invoice_process()
    result = assess_process(process)
    (step,) = result.steps
    assert step.method.method is AutomationMethod.API_INTEGRATION
    assert step.human_control.control is HumanControl.RECOMMENDED
    # 20 frequency + 20 repetitive + 10 rules + 8 unstructured + 10 exceptions + 10 integration
    # - 10 sensitive data
    assert step.score.score == 68
    assert result.process_score == Decimal(68)
    assert result.policy_version == "scoring-v1"
