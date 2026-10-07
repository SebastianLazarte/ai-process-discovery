"""Automation blueprint: the analysis rewritten as something a team could estimate and build."""

from decimal import Decimal

from app.domain.enums import AutomationMethod, HumanControl
from app.domain.reconciliation import RecommendationSource
from app.models.schemas.analysis import AnalysisRead, Blueprint, BlueprintStep, StepAssessmentOut
from app.models.schemas.process import ProcessRead

_COMPONENT_BY_METHOD = {
    AutomationMethod.RULE_BASED: (
        "Rules step in the workflow engine with explicit, versioned validation rules"
    ),
    AutomationMethod.API_INTEGRATION: "API connectors to the systems already in use",
    AutomationMethod.AI_CANDIDATE: (
        "Model-based extraction or classification behind a schema-validated contract"
    ),
    AutomationMethod.HYBRID: "Automated draft with a person confirming the result",
}


def build_blueprint(analysis: AnalysisRead, process: ProcessRead) -> Blueprint:
    steps_by_hours = sorted(analysis.step_assessments, key=lambda s: s.monthly_hours, reverse=True)
    opportunities = [
        BlueprintStep(
            position=step.position,
            name=step.name,
            method=step.final_method,
            human_control=step.final_human_control,
            decided_by=step.final_source,
            monthly_hours=step.monthly_hours,
            suitability_score=step.suitability_score,
            rationale=_rationale(step),
        )
        for step in steps_by_hours
        if step.final_method is not AutomationMethod.MANUAL
    ]

    return Blueprint(
        analysis_id=analysis.id,
        process_summary={
            "name": process.name,
            "description": process.description,
            "owner": process.owner,
            "executions_per_month": process.executions_per_month,
            "steps": len(process.steps),
            "process_version": analysis.process_version,
            "analysed_at": analysis.created_at.isoformat(),
            "rules_version": analysis.rules_version,
            "llm": f"{analysis.llm.status}"
            + (f" ({analysis.llm.provider}/{analysis.llm.model})" if analysis.llm.model else ""),
        },
        current_state=analysis.current_state,
        automation_opportunities=opportunities,
        proposed_architecture=_architecture(analysis),
        business_impact=analysis.business_impact,
        risks=analysis.risks,
        human_controls=analysis.human_controls,
        workflow_specification=_workflow(analysis),
    )


_SUITABILITY_NOTE = (
    "Ordered by monthly time. Suitability measures whether a step can be automated, "
    "not how much it is worth."
)


def render_markdown(blueprint: Blueprint) -> str:
    summary = blueprint.process_summary
    impact = blueprint.business_impact
    analysis_line = (
        f"- **Analysis:** {summary['analysed_at']}, process version {summary['process_version']}, "
        f"rules {summary['rules_version']}, LLM {summary['llm']}"
    )
    lines = [
        f"# Automation blueprint: {summary['name']}",
        "",
        "## Process summary",
        "",
        f"- **Description:** {summary['description'] or 'not given'}",
        f"- **Owner:** {summary['owner'] or 'not given'}",
        f"- **Executions per month:** {summary['executions_per_month']}",
        f"- **Steps:** {summary['steps']}",
        analysis_line,
        "",
        "## Current state",
        "",
        f"- **Monthly hours:** {blueprint.current_state.monthly_hours}",
        f"- **Monthly cost:** {_money(blueprint.current_state.monthly_cost)}",
        "",
        "## Automation opportunities",
        "",
        _SUITABILITY_NOTE,
        "",
        "| # | Step | Method | Human control | Decided by | Hours/month | Suitability |",
        "|---|---|---|---|---|---:|---:|",
    ]
    lines += [
        f"| {s.position} | {s.name} | {s.method} | {s.human_control} | {s.decided_by} | "
        f"{s.monthly_hours} | {s.suitability_score} |"
        for s in blueprint.automation_opportunities
    ]
    lines += ["", *[f"- **{s.name}:** {s.rationale}" for s in blueprint.automation_opportunities]]
    lines += [
        "",
        "## Proposed architecture",
        "",
        *[f"- {c}" for c in blueprint.proposed_architecture],
    ]
    lines += [
        "",
        "## Business impact",
        "",
        "Every economic figure below depends on the assumptions listed after it.",
        "",
        f"- **Hours freed per month:** {impact.estimated_hours_saved}",
        f"- **Gross monthly savings:** {_money(impact.estimated_monthly_savings)}",
        f"- **Monthly tooling cost:** {_money(impact.monthly_tooling_cost)}",
        f"- **Net monthly savings:** {_money(impact.net_monthly_savings)}",
        f"- **Implementation cost:** {_money(impact.implementation_cost)}",
        f"- **Payback (months):** {_value(impact.payback_months)}",
        f"- **ROI at 12 months:** {_percent(impact.roi_12_months)}",
        "",
        "**Assumptions**",
        "",
        f"- Implementation cost: {_money(impact.assumptions.implementation_cost)}",
        f"- Monthly tooling cost: {_money(impact.assumptions.monthly_tooling_cost)}",
    ]
    for step_id, reduction in impact.assumptions.expected_time_reduction_by_step.items():
        lines.append(f"- Expected time reduction for step {step_id}: {_percent(reduction)}")
    if impact.steps_without_reduction:
        lines.append(
            f"- {len(impact.steps_without_reduction)} step(s) have no expected reduction "
            "and count as zero savings"
        )
    lines += ["", "## Risks", ""]
    lines += [f"- [{r.source} / {r.type}] {r.description}" for r in blueprint.risks] or [
        "- None recorded"
    ]
    lines += ["", "## Human controls", ""]
    lines += [
        f"- **{c.step_name}:** {c.control}. {'; '.join(c.reasons)}"
        for c in blueprint.human_controls
    ] or ["- None required"]
    lines += ["", "## Workflow specification", ""]
    lines += [f"{i}. {line}" for i, line in enumerate(blueprint.workflow_specification, start=1)]
    return "\n".join(lines) + "\n"


def _rationale(step: StepAssessmentOut) -> str:
    if step.final_source is RecommendationSource.HUMAN and step.override is not None:
        return f"Reviewer override: {step.override.reason}"
    if step.final_source is RecommendationSource.AI and step.ai_suggestion is not None:
        return step.ai_suggestion.rationale
    return step.rules_method_reason


def _architecture(analysis: AnalysisRead) -> list[str]:
    methods = {s.final_method for s in analysis.step_assessments}
    components = ["Workflow engine that runs the steps in order, with retries and an audit log"]
    components += [text for method, text in _COMPONENT_BY_METHOD.items() if method in methods]
    if any(s.final_human_control is not HumanControl.NONE for s in analysis.step_assessments):
        components.append("Human review queue: flagged items wait for a decision, which is logged")
    components += analysis.architecture_recommendations
    return list(dict.fromkeys(components))


def _workflow(analysis: AnalysisRead) -> list[str]:
    lines = ["Trigger: a new process execution starts"]
    for step in sorted(analysis.step_assessments, key=lambda s: s.position):
        line = f"{step.name}: {step.final_method}"
        if step.final_human_control is HumanControl.REQUIRED:
            line += ", then wait for a person to approve before continuing"
        elif step.final_human_control is HumanControl.RECOMMENDED:
            line += ", with a person reviewing a sample or the flagged cases"
        lines.append(line)
    lines.append("End: record the outcome and the time spent for later comparison")
    return lines


def _money(value: Decimal | None) -> str:
    return "unknown" if value is None else f"{value:,.2f}"


def _value(value: Decimal | None) -> str:
    return "not applicable" if value is None else str(value)


def _percent(value: Decimal | None) -> str:
    return "not applicable" if value is None else f"{value * 100:.0f} %"
