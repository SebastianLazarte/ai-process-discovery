"""Contracts at the LLM boundary.

``LLMAnalysisOutput`` has no field for hours, cost, scores, savings, payback or ROI.
Telling the model not to compute them is weaker than giving it nowhere to put them.
"""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

SuggestedMethod = Literal["RULE_BASED", "API_INTEGRATION", "AI_CANDIDATE", "HYBRID", "MANUAL"]
RiskType = Literal["TECHNICAL", "OPERATIONAL", "DATA", "AI"]


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class LLMStepAssessment(_Strict):
    step_id: str
    interpretation: str
    suggested_method: SuggestedMethod
    confidence: float = Field(ge=0, le=1)
    rationale: str
    dependencies: list[str]
    risks: list[str]
    human_control_recommended: bool
    uncertainties: list[str]


class LLMProcessRisk(_Strict):
    type: RiskType
    description: str


class LLMAnalysisOutput(_Strict):
    step_assessments: list[LLMStepAssessment]
    architecture_recommendations: list[str]
    process_risks: list[LLMProcessRisk]
    unknowns: list[str]


# Input side: what the model is allowed to see. No money, no hours.


class LLMStepContext(_Strict):
    step_id: str
    position: int
    name: str
    description: str
    responsible_role: str
    tools: list[str]
    input_description: str
    output_description: str
    problems: list[str]
    repetitiveness: str
    rule_clarity: str
    input_type: str
    integration_readiness: str
    criticality: str
    requires_human_judgement: bool
    requires_human_approval: bool
    handles_sensitive_data: bool
    rules_method: str
    rules_human_control: str
    automation_score: int


class LLMAnalysisRequest(_Strict):
    process_name: str
    process_description: str
    steps: list[LLMStepContext]


# Field names the output schema must never contain (RS-27).
FORBIDDEN_OUTPUT_FIELDS = frozenset(
    {
        "monthly_hours",
        "monthly_cost",
        "automation_score",
        "score",
        "estimated_hours_saved",
        "estimated_monthly_savings",
        "savings",
        "payback",
        "payback_months",
        "roi",
        "roi_12_months",
        "cost",
        "hours",
    }
)
