"""Deterministic provider for demos, CI and tests. No network, no key."""

from collections.abc import Callable

from app.llm.provider import LLMProviderError
from app.llm.schemas import (
    LLMAnalysisOutput,
    LLMAnalysisRequest,
    LLMProcessRisk,
    LLMStepAssessment,
    SuggestedMethod,
)

_METHOD_BY_RULE: dict[str, SuggestedMethod] = {
    "RULE_BASED": "RULE_BASED",
    "API_INTEGRATION": "API_INTEGRATION",
    "AI_CANDIDATE": "AI_CANDIDATE",
    "MANUAL": "MANUAL",
    "NEEDS_REVIEW": "HYBRID",
}


class FakeLLMProvider:
    """Answers from the rules context with fixed wording.

    Tests can inject a ``responder`` to return a specific output, or an ``error`` to raise.
    """

    def __init__(
        self,
        responder: Callable[[LLMAnalysisRequest], LLMAnalysisOutput] | None = None,
        error: LLMProviderError | None = None,
    ) -> None:
        self._responder = responder
        self._error = error
        self.calls: list[LLMAnalysisRequest] = []

    @property
    def name(self) -> str:
        return "fake"

    @property
    def model(self) -> str:
        return "fake-deterministic-v1"

    def analyze_process(self, request: LLMAnalysisRequest) -> LLMAnalysisOutput:
        self.calls.append(request)
        if self._error is not None:
            raise self._error
        if self._responder is not None:
            return self._responder(request)
        return _default_answer(request)


def _default_answer(request: LLMAnalysisRequest) -> LLMAnalysisOutput:
    steps = []
    for step in request.steps:
        method = _METHOD_BY_RULE.get(step.rules_method, "HYBRID")
        risks = (
            ["Data protection: restrict access and log processing"]
            if (step.handles_sensitive_data)
            else []
        )
        dependencies = [f"Access to {tool}" for tool in step.tools]
        steps.append(
            LLMStepAssessment(
                step_id=step.step_id,
                interpretation=f"{step.name}: {step.description or 'no description given'}",
                suggested_method=method,
                confidence=0.6,
                rationale=(
                    f"Input is {step.input_type.lower().replace('_', ' ')} and integration "
                    f"readiness is {step.integration_readiness.lower()}."
                ),
                dependencies=dependencies,
                risks=risks,
                human_control_recommended=step.handles_sensitive_data
                or step.rules_human_control != "NONE",
                uncertainties=(
                    ["Exception handling is not described"]
                    if step.rules_method == "NEEDS_REVIEW"
                    else []
                ),
            )
        )
    return LLMAnalysisOutput(
        step_assessments=steps,
        architecture_recommendations=[
            "Orchestrate the automated steps from a single workflow engine with retries",
            "Route low-confidence and flagged items to a human review queue",
        ],
        process_risks=[
            LLMProcessRisk(
                type="OPERATIONAL",
                description="Exceptions need an owner once the happy path is automated",
            )
        ],
        unknowns=[],
    )
