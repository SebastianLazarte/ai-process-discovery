"""HTTP contracts for analyses, overrides and blueprints.

The response keeps suitability, business impact, risk and human controls in separate
sections. There is no single combined "AI score".
"""

from datetime import datetime
from decimal import Decimal
from typing import Literal, Self
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.domain.enums import AutomationMethod, HumanControl
from app.domain.reconciliation import RecommendationSource


class _Schema(BaseModel):
    model_config = ConfigDict(extra="forbid")


class BusinessCaseInput(_Schema):
    implementation_cost: Decimal | None = Field(default=None, ge=0)
    monthly_tooling_cost: Decimal = Field(default=Decimal(0), ge=0)
    expected_time_reduction_by_step: dict[UUID, Decimal] = Field(
        default_factory=dict,
        description="Expected share of each step's time removed by automation, from 0 to 1.",
    )


class AnalysisCreate(_Schema):
    assumptions: BusinessCaseInput = Field(default_factory=BusinessCaseInput)
    use_llm: bool = False
    confirm_sensitive: bool = Field(
        default=False,
        description="Required when use_llm is true and any step handles sensitive data.",
    )


class ScoreFactorOut(_Schema):
    name: str
    points: int
    max_points: int
    detail: str


class ScorePenaltyOut(_Schema):
    name: str
    points: int


class AISuggestionOut(_Schema):
    method: AutomationMethod
    confidence: float
    interpretation: str
    rationale: str
    human_control_recommended: bool
    dependencies: list[str]
    risks: list[str]
    uncertainties: list[str]


class OverrideOut(_Schema):
    id: UUID
    step_id: UUID
    original_method: AutomationMethod
    original_human_control: HumanControl
    new_method: AutomationMethod
    new_human_control: HumanControl
    reason: str
    created_at: datetime


class StepAssessmentOut(_Schema):
    step_id: UUID
    position: int
    name: str
    monthly_hours: Decimal
    suitability_score: int
    score_factors: list[ScoreFactorOut]
    score_penalties: list[ScorePenaltyOut]
    score_unknowns: list[str]
    rules_method: AutomationMethod
    rules_method_reason: str
    rules_human_control: HumanControl
    human_control_reasons: list[str]
    ai_suggestion: AISuggestionOut | None
    final_method: AutomationMethod
    final_human_control: HumanControl
    final_source: RecommendationSource
    reconciliation_notes: list[str]
    override: OverrideOut | None = None


class CurrentStateOut(_Schema):
    monthly_hours: Decimal
    monthly_cost: Decimal | None


class SuitabilityOut(_Schema):
    process_score: Decimal | None = Field(description="Time-weighted mean of step scores, 0-100.")
    policy_version: str


class BusinessImpactOut(_Schema):
    estimated_hours_saved: Decimal
    estimated_monthly_savings: Decimal | None
    monthly_tooling_cost: Decimal
    net_monthly_savings: Decimal | None
    implementation_cost: Decimal | None
    payback_months: Decimal | None
    roi_12_months: Decimal | None
    assumptions: BusinessCaseInput
    steps_without_reduction: list[UUID]


class RiskOut(_Schema):
    source: Literal["RULES", "AI"]
    type: str
    description: str
    step_id: UUID | None = None


class HumanControlOut(_Schema):
    step_id: UUID
    step_name: str
    control: HumanControl
    reasons: list[str]


LLMStatus = Literal["not_requested", "ok", "unavailable"]


class LLMInfo(_Schema):
    status: LLMStatus
    provider: str | None
    model: str | None
    prompt_version: str | None
    error_kind: str | None = None


class AnalysisRead(_Schema):
    id: UUID
    process_id: UUID
    process_version: int
    created_at: datetime
    rules_version: str
    llm: LLMInfo
    current_state: CurrentStateOut
    automation_suitability: SuitabilityOut
    business_impact: BusinessImpactOut
    risks: list[RiskOut]
    human_controls: list[HumanControlOut]
    step_assessments: list[StepAssessmentOut]
    architecture_recommendations: list[str]
    unknowns: list[str]


class AnalysisSummary(_Schema):
    id: UUID
    created_at: datetime
    process_version: int
    rules_version: str
    llm_status: LLMStatus
    provider: str | None
    model: str | None
    override_count: int


class OverrideCreate(_Schema):
    step_id: UUID
    method: AutomationMethod | None = None
    human_control: HumanControl | None = None
    reason: str = Field(min_length=3, max_length=2000)

    @model_validator(mode="after")
    def _changes_something(self) -> Self:
        if self.method is None and self.human_control is None:
            raise ValueError("set method, human_control or both")
        return self


class BlueprintStep(_Schema):
    position: int
    name: str
    method: AutomationMethod
    human_control: HumanControl
    decided_by: RecommendationSource
    monthly_hours: Decimal
    suitability_score: int
    rationale: str


class Blueprint(_Schema):
    analysis_id: UUID
    process_summary: dict[str, str | int | None]
    current_state: CurrentStateOut
    automation_opportunities: list[BlueprintStep]
    proposed_architecture: list[str]
    business_impact: BusinessImpactOut
    risks: list[RiskOut]
    human_controls: list[HumanControlOut]
    workflow_specification: list[str]
