from typing import Any

import pytest
from pydantic import ValidationError

from app.llm.prompts import PROMPT_VERSION, SYSTEM_PROMPT, build_user_prompt
from app.llm.providers.fake import FakeLLMProvider
from app.llm.schemas import (
    FORBIDDEN_OUTPUT_FIELDS,
    LLMAnalysisOutput,
    LLMAnalysisRequest,
    LLMStepContext,
)


def _property_names(schema: Any) -> set[str]:
    names: set[str] = set()
    if isinstance(schema, dict):
        for key, value in schema.items():
            if key == "properties" and isinstance(value, dict):
                names.update(value)
            names |= _property_names(value)
    elif isinstance(schema, list):
        for item in schema:
            names |= _property_names(item)
    return names


def test_output_schema_has_no_place_for_business_numbers() -> None:
    names = _property_names(LLMAnalysisOutput.model_json_schema())
    assert names & FORBIDDEN_OUTPUT_FIELDS == set()
    assert "step_assessments" in names


def test_output_rejects_extra_fields() -> None:
    with pytest.raises(ValidationError):
        LLMAnalysisOutput.model_validate(
            {
                "step_assessments": [],
                "architecture_recommendations": [],
                "process_risks": [],
                "unknowns": [],
                "monthly_hours": 30,
            }
        )


def test_output_rejects_out_of_range_confidence() -> None:
    with pytest.raises(ValidationError):
        LLMAnalysisOutput.model_validate(
            {
                "step_assessments": [
                    {
                        "step_id": "s",
                        "interpretation": "i",
                        "suggested_method": "MANUAL",
                        "confidence": 1.5,
                        "rationale": "r",
                        "dependencies": [],
                        "risks": [],
                        "human_control_recommended": True,
                        "uncertainties": [],
                    }
                ],
                "architecture_recommendations": [],
                "process_risks": [],
                "unknowns": [],
            }
        )


def _request(**overrides: Any) -> LLMAnalysisRequest:
    step: dict[str, Any] = {
        "step_id": "abc",
        "position": 1,
        "name": "Match",
        "description": "Match invoice",
        "responsible_role": "AP",
        "tools": ["ERP"],
        "input_description": "",
        "output_description": "",
        "problems": [],
        "repetitiveness": "HIGH",
        "rule_clarity": "MEDIUM",
        "input_type": "DIGITAL_STRUCTURED",
        "integration_readiness": "PARTIAL",
        "criticality": "MEDIUM",
        "requires_human_judgement": False,
        "requires_human_approval": False,
        "handles_sensitive_data": False,
        "rules_method": "NEEDS_REVIEW",
        "rules_human_control": "NONE",
        "automation_score": 60,
    }
    step.update(overrides)
    return LLMAnalysisRequest(
        process_name="P", process_description="D", steps=[LLMStepContext(**step)]
    )


def test_fake_provider_is_deterministic() -> None:
    provider = FakeLLMProvider()
    assert provider.analyze_process(_request()) == provider.analyze_process(_request())
    assert provider.name == "fake"


def test_fake_provider_flags_sensitive_steps() -> None:
    output = FakeLLMProvider().analyze_process(_request(handles_sensitive_data=True))
    (step,) = output.step_assessments
    assert step.human_control_recommended is True
    assert step.risks


def test_prompt_is_versioned_and_states_the_boundary() -> None:
    assert PROMPT_VERSION
    assert "do not produce them" in SYSTEM_PROMPT
    assert "Never recommend removing a human control" in SYSTEM_PROMPT
    assert '"step_id": "abc"' in build_user_prompt(_request())
