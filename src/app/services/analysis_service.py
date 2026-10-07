"""Runs an analysis: deterministic engine first, LLM enrichment second, reconciliation last.

Authority order (spec RN-01): system facts > user-confirmed facts > LLM suggestions.
"""

import logging
from collections.abc import Callable, Sequence
from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy.orm import Session

from app.core.errors import AppError, NotFoundError, SensitiveDataConfirmationError
from app.domain.assessment import DeterministicAssessment, assess_process
from app.domain.business_case import BusinessCase, BusinessCaseAssumptions, calculate_business_case
from app.domain.decimals import present_hours, present_money, present_ratio, present_score
from app.domain.entities import Process, ProcessStep
from app.domain.enums import AutomationMethod, HumanControl, Level
from app.domain.policies import DEFAULT_POLICY, ScoringPolicy
from app.domain.reconciliation import AISuggestion, RecommendationSource, reconcile
from app.llm.prompts import PROMPT_VERSION
from app.llm.provider import LLMProvider, LLMProviderError
from app.llm.schemas import LLMAnalysisOutput, LLMAnalysisRequest, LLMStepContext
from app.models.persistence import AnalysisORM, OverrideORM
from app.models.schemas.analysis import (
    AISuggestionOut,
    AnalysisCreate,
    AnalysisRead,
    AnalysisSummary,
    BusinessCaseInput,
    BusinessImpactOut,
    CurrentStateOut,
    HumanControlOut,
    LLMInfo,
    LLMStatus,
    OverrideCreate,
    OverrideOut,
    RiskOut,
    ScoreFactorOut,
    ScorePenaltyOut,
    StepAssessmentOut,
    SuitabilityOut,
)
from app.models.schemas.process import ProcessRead
from app.repositories.analysis_repository import AnalysisRepository
from app.repositories.process_repository import ProcessRepository, to_domain

logger = logging.getLogger(__name__)


class AnalysisService:
    def __init__(
        self, session: Session, provider: LLMProvider, policy: ScoringPolicy = DEFAULT_POLICY
    ) -> None:
        self._session = session
        self._processes = ProcessRepository(session)
        self._analyses = AnalysisRepository(session)
        self._provider = provider
        self._policy = policy

    # Commands

    def run(self, process_id: UUID, request: AnalysisCreate) -> AnalysisRead:
        stored = self._processes.get(process_id)
        if stored is None:
            raise NotFoundError(f"process {process_id} not found")
        snapshot = ProcessRead.model_validate(stored)
        process = to_domain(stored)

        deterministic = assess_process(process, self._policy)
        assumptions = _to_assumptions(request.assumptions)
        business_case = calculate_business_case(process, assumptions)

        llm_status: LLMStatus = "not_requested"
        error_kind: str | None = None
        ai_output: LLMAnalysisOutput | None = None
        if request.use_llm:
            sensitive = [s.name for s in process.steps if s.handles_sensitive_data]
            if sensitive and not request.confirm_sensitive:
                raise SensitiveDataConfirmationError(
                    "these steps handle sensitive data and would be sent to the LLM provider: "
                    + ", ".join(sensitive)
                    + ". Resend with confirm_sensitive=true to proceed."
                )
            try:
                ai_output = self._provider.analyze_process(_llm_request(process, deterministic))
                llm_status = "ok"
            except LLMProviderError as exc:
                llm_status, error_kind = "unavailable", exc.kind
                logger.warning(
                    "llm_unavailable",
                    extra={"process_id": str(process_id), "error_kind": exc.kind},
                )

        analysis = _build_analysis(
            process=process,
            snapshot=snapshot,
            deterministic=deterministic,
            business_case=business_case,
            assumptions=request.assumptions,
            ai_output=ai_output,
            llm=LLMInfo(
                status=llm_status,
                provider=self._provider.name if request.use_llm else None,
                model=self._provider.model if request.use_llm else None,
                prompt_version=PROMPT_VERSION if request.use_llm else None,
                error_kind=error_kind,
            ),
        )
        self._analyses.add(
            AnalysisORM(
                id=analysis.id,
                process_id=process.id,
                process_version=snapshot.version,
                rules_version=analysis.rules_version,
                prompt_version=analysis.llm.prompt_version,
                provider=analysis.llm.provider,
                model=analysis.llm.model,
                llm_status=llm_status,
                created_at=analysis.created_at,
                process_snapshot=snapshot.model_dump(mode="json"),
                result=analysis.model_dump(mode="json"),
            )
        )
        self._session.commit()
        logger.info(
            "analysis_created",
            extra={
                "analysis_id": str(analysis.id),
                "process_id": str(process.id),
                "steps": len(process.steps),
                "llm_status": llm_status,
            },
        )
        return analysis

    def add_override(self, analysis_id: UUID, data: OverrideCreate) -> AnalysisRead:
        stored = self._get(analysis_id)
        original = AnalysisRead.model_validate(stored.result)
        step = next((s for s in original.step_assessments if s.step_id == data.step_id), None)
        if step is None:
            raise AppError(f"step {data.step_id} is not part of analysis {analysis_id}")
        current = apply_overrides(original, stored.overrides)
        current_step = next(s for s in current.step_assessments if s.step_id == data.step_id)
        self._analyses.add_override(
            OverrideORM(
                analysis_id=stored.id,
                step_id=data.step_id,
                original_method=step.final_method.value,
                original_human_control=step.final_human_control.value,
                new_method=(data.method or current_step.final_method).value,
                new_human_control=(data.human_control or current_step.final_human_control).value,
                reason=data.reason,
            )
        )
        self._session.commit()
        self._session.refresh(stored)
        logger.info("override_created", extra={"analysis_id": str(analysis_id)})
        return apply_overrides(original, stored.overrides)

    # Queries

    def get(self, analysis_id: UUID) -> AnalysisRead:
        stored = self._get(analysis_id)
        return apply_overrides(AnalysisRead.model_validate(stored.result), stored.overrides)

    def get_snapshot(self, analysis_id: UUID) -> ProcessRead:
        return ProcessRead.model_validate(self._get(analysis_id).process_snapshot)

    def list_for_process(self, process_id: UUID) -> list[AnalysisSummary]:
        if self._processes.get(process_id) is None:
            raise NotFoundError(f"process {process_id} not found")
        return [
            AnalysisSummary(
                id=row.id,
                created_at=row.created_at,
                process_version=row.process_version,
                rules_version=row.rules_version,
                llm_status=row.result["llm"]["status"],
                provider=row.provider,
                model=row.model,
                override_count=len(row.overrides),
            )
            for row in self._analyses.list_for_process(process_id)
        ]

    def _get(self, analysis_id: UUID) -> AnalysisORM:
        stored = self._analyses.get(analysis_id)
        if stored is None:
            raise NotFoundError(f"analysis {analysis_id} not found")
        return stored


def apply_overrides(analysis: AnalysisRead, overrides: Sequence[OverrideORM]) -> AnalysisRead:
    """Return the analysis as a reviewer sees it: latest human decision per step wins."""
    latest: dict[UUID, OverrideORM] = {}
    for item in sorted(overrides, key=lambda o: o.created_at):
        latest[item.step_id] = item
    if not latest:
        return analysis

    steps = []
    for step in analysis.step_assessments:
        override = latest.get(step.step_id)
        if override is None:
            steps.append(step)
            continue
        steps.append(
            step.model_copy(
                update={
                    "final_method": AutomationMethod(override.new_method),
                    "final_human_control": HumanControl(override.new_human_control),
                    "final_source": RecommendationSource.HUMAN,
                    "override": OverrideOut(
                        id=override.id,
                        step_id=override.step_id,
                        original_method=AutomationMethod(override.original_method),
                        original_human_control=HumanControl(override.original_human_control),
                        new_method=AutomationMethod(override.new_method),
                        new_human_control=HumanControl(override.new_human_control),
                        reason=override.reason,
                        created_at=override.created_at,
                    ),
                }
            )
        )
    return analysis.model_copy(
        update={"step_assessments": steps, "human_controls": _human_controls(steps)}
    )


def _to_assumptions(data: BusinessCaseInput) -> BusinessCaseAssumptions:
    return BusinessCaseAssumptions(
        implementation_cost=data.implementation_cost,
        monthly_tooling_cost=data.monthly_tooling_cost,
        expected_time_reduction_by_step=data.expected_time_reduction_by_step,
    )


def _llm_request(process: Process, deterministic: DeterministicAssessment) -> LLMAnalysisRequest:
    by_id = {a.step_id: a for a in deterministic.steps}
    return LLMAnalysisRequest(
        process_name=process.name,
        process_description=process.description,
        steps=[
            LLMStepContext(
                step_id=str(step.id),
                position=step.position,
                name=step.name,
                description=step.description,
                responsible_role=step.responsible_role,
                tools=list(step.tools),
                input_description=step.input_description,
                output_description=step.output_description,
                problems=list(step.problems),
                repetitiveness=step.repetitiveness.value,
                rule_clarity=step.rule_clarity.value,
                input_type=step.input_type.value,
                integration_readiness=step.integration_readiness.value,
                criticality=step.criticality.value,
                requires_human_judgement=step.requires_human_judgement,
                requires_human_approval=step.requires_human_approval,
                handles_sensitive_data=step.handles_sensitive_data,
                rules_method=by_id[step.id].method.method.value,
                rules_human_control=by_id[step.id].human_control.control.value,
                automation_score=by_id[step.id].score.score,
            )
            for step in process.steps
        ],
    )


def _ai_suggestions(process: Process, output: LLMAnalysisOutput | None) -> dict[UUID, AISuggestion]:
    if output is None:
        return {}
    known = {str(step.id): step.id for step in process.steps}
    suggestions: dict[UUID, AISuggestion] = {}
    discarded = 0
    for item in output.step_assessments:
        step_id = known.get(item.step_id)
        if step_id is None:
            discarded += 1
            continue
        suggestions[step_id] = AISuggestion(
            method=AutomationMethod(item.suggested_method),
            confidence=item.confidence,
            interpretation=item.interpretation,
            rationale=item.rationale,
            human_control_recommended=item.human_control_recommended,
            dependencies=tuple(item.dependencies),
            risks=tuple(item.risks),
            uncertainties=tuple(item.uncertainties),
        )
    if discarded:
        logger.warning("llm_unknown_steps_discarded", extra={"count": discarded})
    return suggestions


def _build_analysis(
    *,
    process: Process,
    snapshot: ProcessRead,
    deterministic: DeterministicAssessment,
    business_case: BusinessCase,
    assumptions: BusinessCaseInput,
    ai_output: LLMAnalysisOutput | None,
    llm: LLMInfo,
) -> AnalysisRead:
    suggestions = _ai_suggestions(process, ai_output)
    steps: list[StepAssessmentOut] = []
    risks: list[RiskOut] = []
    unknowns: list[str] = []

    for rules in deterministic.steps:
        step = process.step(rules.step_id)
        ai = suggestions.get(step.id)
        final = reconcile(rules, ai)
        steps.append(
            StepAssessmentOut(
                step_id=step.id,
                position=step.position,
                name=step.name,
                monthly_hours=present_hours(rules.monthly_hours),
                suitability_score=rules.score.score,
                score_factors=[
                    ScoreFactorOut(
                        name=f.name, points=f.points, max_points=f.max_points, detail=f.detail
                    )
                    for f in rules.score.factors
                ],
                score_penalties=[
                    ScorePenaltyOut(name=p.name, points=p.points) for p in rules.score.penalties
                ],
                score_unknowns=list(rules.score.unknowns),
                rules_method=rules.method.method,
                rules_method_reason=rules.method.reason,
                rules_human_control=rules.human_control.control,
                human_control_reasons=list(rules.human_control.reasons),
                ai_suggestion=_ai_out(ai),
                final_method=final.method,
                final_human_control=final.human_control,
                final_source=final.source,
                reconciliation_notes=list(final.notes),
            )
        )
        risks.extend(_rule_risks(step))
        if ai is not None:
            risks.extend(
                RiskOut(source="AI", type="STEP", description=text, step_id=step.id)
                for text in ai.risks
            )
        unknowns.extend(f"{step.name}: {field} is unknown" for field in rules.score.unknowns)

    if ai_output is not None:
        risks.extend(
            RiskOut(source="AI", type=r.type, description=r.description)
            for r in ai_output.process_risks
        )
        unknowns.extend(f"AI: {text}" for text in ai_output.unknowns)

    for step_id in business_case.steps_without_reduction:
        unknowns.append(f"{process.step(step_id).name}: no expected time reduction given")

    state = deterministic.current_state
    return AnalysisRead(
        id=uuid4(),
        process_id=process.id,
        process_version=snapshot.version,
        created_at=datetime.now(UTC),
        rules_version=deterministic.policy_version,
        llm=llm,
        current_state=CurrentStateOut(
            monthly_hours=present_hours(state.monthly_hours),
            monthly_cost=_maybe(present_money, state.monthly_cost),
        ),
        automation_suitability=SuitabilityOut(
            process_score=_maybe(present_score, deterministic.process_score),
            policy_version=deterministic.policy_version,
        ),
        business_impact=BusinessImpactOut(
            estimated_hours_saved=present_hours(business_case.estimated_hours_saved),
            estimated_monthly_savings=_maybe(
                present_money, business_case.estimated_monthly_savings
            ),
            monthly_tooling_cost=present_money(business_case.monthly_tooling_cost),
            net_monthly_savings=_maybe(present_money, business_case.net_monthly_savings),
            implementation_cost=_maybe(present_money, business_case.implementation_cost),
            payback_months=_maybe(present_ratio, business_case.payback_months),
            roi_12_months=_maybe(present_ratio, business_case.roi_12_months),
            assumptions=assumptions,
            steps_without_reduction=list(business_case.steps_without_reduction),
        ),
        risks=risks,
        human_controls=_human_controls(steps),
        step_assessments=steps,
        architecture_recommendations=list(ai_output.architecture_recommendations)
        if ai_output
        else [],
        unknowns=unknowns,
    )


def _ai_out(ai: AISuggestion | None) -> AISuggestionOut | None:
    if ai is None:
        return None
    return AISuggestionOut(
        method=ai.method,
        confidence=ai.confidence,
        interpretation=ai.interpretation,
        rationale=ai.rationale,
        human_control_recommended=ai.human_control_recommended,
        dependencies=list(ai.dependencies),
        risks=list(ai.risks),
        uncertainties=list(ai.uncertainties),
    )


def _rule_risks(step: ProcessStep) -> list[RiskOut]:
    found = []
    if step.handles_sensitive_data:
        found.append(("DATA", f"{step.name} handles sensitive data"))
    if step.criticality is Level.HIGH:
        found.append(("OPERATIONAL", f"{step.name} is business critical"))
    if step.requires_human_judgement:
        found.append(("OPERATIONAL", f"{step.name} depends on human judgement"))
    return [
        RiskOut(source="RULES", type=kind, description=text, step_id=step.id)
        for kind, text in found
    ]


def _human_controls(steps: Sequence[StepAssessmentOut]) -> list[HumanControlOut]:
    controls = []
    for step in steps:
        if step.final_human_control is HumanControl.NONE:
            continue
        reasons = list(step.human_control_reasons)
        reasons.extend(note for note in step.reconciliation_notes if "human control" in note)
        if step.override is not None:
            reasons.append(f"Reviewer decision: {step.override.reason}")
        controls.append(
            HumanControlOut(
                step_id=step.step_id,
                step_name=step.name,
                control=step.final_human_control,
                reasons=reasons,
            )
        )
    return controls


def _maybe(present: Callable[[Decimal], Decimal], value: Decimal | None) -> Decimal | None:
    return None if value is None else present(value)
