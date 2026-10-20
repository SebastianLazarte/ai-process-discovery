// Typed factories for the API payloads that tests answer with. Each one returns a complete,
// valid object as the API would send it, and takes overrides for what a test cares about.
// Figures are strings, as the API sends decimals; the client prints them and computes none.
import type { components } from "@/lib/api/schema";

type Schemas = components["schemas"];
export type ProcessSummary = Schemas["ProcessSummary"];
export type ProcessRead = Schemas["ProcessRead"];
export type StepRead = Schemas["StepRead"];
export type StepCreate = Schemas["StepCreate"];
export type DemoSummary = Schemas["DemoSummary"];
export type AnalysisSummary = Schemas["AnalysisSummary"];
export type AnalysisRead = Schemas["AnalysisRead"];
export type StepAssessment = Schemas["StepAssessmentOut"];
export type Blueprint = Schemas["Blueprint"];

export const PROCESS_ID = "11111111-1111-4111-8111-111111111111";
export const STEP_ID = "55555555-5555-4555-8555-555555555555";
export const ANALYSIS_ID = "66666666-6666-4666-8666-666666666666";

export function processSummary(overrides: Partial<ProcessSummary> = {}): ProcessSummary {
  return {
    id: PROCESS_ID,
    name: "Warranty claims from installers",
    owner: "After-sales",
    executions_per_month: 180,
    step_count: 7,
    version: 1,
    updated_at: "2026-10-16T09:30:00Z",
    ...overrides,
  };
}

/** The fields of a step as a form sends them, without the id and position the API assigns. */
export function stepFields(overrides: Partial<StepCreate> = {}): StepCreate {
  return {
    name: "Read the claim email",
    description: "",
    responsible_role: "Claims clerk",
    tools: ["Outlook"],
    input_description: "",
    output_description: "",
    minutes_per_execution: "4",
    occurrence_rate: "1",
    repetitiveness: "HIGH",
    rule_clarity: "MEDIUM",
    input_type: "DIGITAL_UNSTRUCTURED",
    exception_rate: null,
    integration_readiness: "PARTIAL",
    requires_human_judgement: false,
    requires_human_approval: false,
    handles_sensitive_data: false,
    criticality: "MEDIUM",
    problems: [],
    ...overrides,
  };
}

/** A stored step: the API answers its figures as decimal strings. */
export function step(overrides: Partial<StepRead> = {}): StepRead {
  return {
    ...stepFields(),
    minutes_per_execution: "4",
    occurrence_rate: "1",
    exception_rate: null,
    id: STEP_ID,
    position: 1,
    ...overrides,
  };
}

export function processRead(overrides: Partial<ProcessRead> = {}): ProcessRead {
  const steps = overrides.steps ?? [];
  return {
    id: PROCESS_ID,
    name: "Warranty claims from installers",
    description: "Installers send claims by email.",
    owner: "After-sales",
    executions_per_month: 180,
    hourly_cost: null,
    version: 1,
    created_at: "2026-10-16T09:00:00Z",
    updated_at: "2026-10-16T09:30:00Z",
    ...overrides,
    steps,
  };
}

export function demo(overrides: Partial<DemoSummary> = {}): DemoSummary {
  return {
    slug: "warranty-claims",
    name: "Warranty claims from installers",
    description: "Installers send warranty claims by email.",
    ...overrides,
  };
}

export function analysisSummary(overrides: Partial<AnalysisSummary> = {}): AnalysisSummary {
  return {
    id: ANALYSIS_ID,
    created_at: "2026-10-16T10:00:00Z",
    process_version: 1,
    rules_version: "1.0.0",
    llm_status: "not_requested",
    provider: null,
    model: null,
    override_count: 0,
    ...overrides,
  };
}

export function stepAssessment(overrides: Partial<StepAssessment> = {}): StepAssessment {
  return {
    step_id: STEP_ID,
    position: 1,
    name: "Read the claim email",
    monthly_hours: "12.00",
    suitability_score: 64,
    score_factors: [
      { name: "repetitiveness", points: 25, max_points: 25, detail: "HIGH" },
      { name: "input_type", points: 5, max_points: 20, detail: "DIGITAL_UNSTRUCTURED" },
    ],
    score_penalties: [],
    score_unknowns: [],
    rules_method: "AI_CANDIDATE",
    rules_method_reason: "Unstructured input with clear enough rules.",
    rules_human_control: "RECOMMENDED",
    human_control_reasons: ["AI output needs a review"],
    ai_suggestion: null,
    final_method: "AI_CANDIDATE",
    final_human_control: "RECOMMENDED",
    final_source: "RULES",
    reconciliation_notes: [],
    override: null,
    ...overrides,
  };
}

export function analysisRead(overrides: Partial<AnalysisRead> = {}): AnalysisRead {
  return {
    id: ANALYSIS_ID,
    process_id: PROCESS_ID,
    process_version: 1,
    created_at: "2026-10-16T10:00:00Z",
    rules_version: "1.0.0",
    llm: {
      status: "not_requested",
      provider: null,
      model: null,
      prompt_version: null,
      error_kind: null,
    },
    current_state: { monthly_hours: "12.00", monthly_cost: null },
    automation_suitability: { process_score: "64", policy_version: "1.0.0" },
    business_impact: {
      estimated_hours_saved: "6.00",
      estimated_monthly_savings: null,
      monthly_tooling_cost: "0",
      net_monthly_savings: null,
      implementation_cost: null,
      payback_months: null,
      roi_12_months: null,
      assumptions: {
        implementation_cost: null,
        monthly_tooling_cost: "0",
        expected_time_reduction_by_step: {},
      },
      steps_without_reduction: [],
    },
    risks: [],
    human_controls: [
      {
        step_id: STEP_ID,
        step_name: "Read the claim email",
        control: "RECOMMENDED",
        reasons: ["AI output needs a review"],
      },
    ],
    step_assessments: [stepAssessment()],
    architecture_recommendations: [],
    unknowns: ["Hourly cost is unknown, so costs and savings stay unknown."],
    ...overrides,
  };
}

export function blueprint(overrides: Partial<Blueprint> = {}): Blueprint {
  const analysis = analysisRead();
  return {
    analysis_id: ANALYSIS_ID,
    process_summary: { name: "Warranty claims from installers", version: 1 },
    current_state: analysis.current_state,
    automation_opportunities: [
      {
        position: 1,
        name: "Read the claim email",
        method: "AI_CANDIDATE",
        human_control: "RECOMMENDED",
        decided_by: "RULES",
        monthly_hours: "12.00",
        suitability_score: 64,
        rationale: "Unstructured input with clear enough rules.",
      },
    ],
    proposed_architecture: [],
    business_impact: analysis.business_impact,
    risks: [],
    human_controls: analysis.human_controls,
    workflow_specification: [],
    ...overrides,
  };
}
