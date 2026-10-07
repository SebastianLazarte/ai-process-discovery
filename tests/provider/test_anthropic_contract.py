"""Contract test against the real Anthropic API.

Excluded from the default run. Execute with `pytest -m llm -o addopts=""` and a key,
or through the manual `llm-contract` workflow.
"""

import pytest

from app.core.config import Settings
from app.llm.providers.anthropic import AnthropicProvider
from app.llm.schemas import LLMAnalysisRequest, LLMStepContext


@pytest.mark.llm
def test_real_provider_returns_valid_structured_output() -> None:
    provider = AnthropicProvider.from_settings(Settings(llm_provider="anthropic"))
    request = LLMAnalysisRequest(
        process_name="Invoice intake",
        process_description="Supplier invoices arrive by email and are keyed into the ERP.",
        steps=[
            LLMStepContext(
                step_id="step-1",
                position=1,
                name="Extract invoice fields",
                description="Copy supplier, number, dates and totals from a PDF into the ERP",
                responsible_role="Finance Assistant",
                tools=["Email", "ERP"],
                input_description="PDF invoice",
                output_description="ERP invoice record",
                problems=["typing errors"],
                repetitiveness="HIGH",
                rule_clarity="MEDIUM",
                input_type="DIGITAL_UNSTRUCTURED",
                integration_readiness="GOOD",
                criticality="MEDIUM",
                requires_human_judgement=False,
                requires_human_approval=True,
                handles_sensitive_data=False,
                rules_method="API_INTEGRATION",
                rules_human_control="REQUIRED",
                automation_score=78,
            )
        ],
    )
    output = provider.analyze_process(request)
    assert [s.step_id for s in output.step_assessments] == ["step-1"]
