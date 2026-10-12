// Minimal API payloads shaped like the FastAPI responses.

export function process({ name = 'Invoice intake', description = '', owner = 'Finance', stepName = 'Extract fields', sensitive = false, steps = 1 } = {}) {
  return {
    id: 'p1',
    name,
    description,
    owner,
    executions_per_month: 400,
    hourly_cost: '18.50',
    version: 1,
    created_at: '2026-10-09T10:00:00Z',
    updated_at: '2026-10-09T10:00:00Z',
    steps: Array.from({ length: steps }, (_, i) => ({
      id: `s${i + 1}`,
      position: i + 1,
      name: stepName,
      description: stepName,
      responsible_role: stepName,
      tools: [stepName],
      input_description: '',
      output_description: '',
      minutes_per_execution: '4.0',
      occurrence_rate: '1',
      repetitiveness: 'HIGH',
      rule_clarity: 'MEDIUM',
      input_type: 'DIGITAL_UNSTRUCTURED',
      exception_rate: '0.08',
      integration_readiness: 'GOOD',
      requires_human_judgement: false,
      requires_human_approval: false,
      handles_sensitive_data: sensitive,
      criticality: 'MEDIUM',
      problems: [],
    })),
  };
}

export function analysis({ stepName = 'Extract fields', llmStatus = 'ok' } = {}) {
  return {
    id: 'a1',
    process_id: 'p1',
    process_version: 1,
    created_at: '2026-10-09T10:00:00Z',
    rules_version: 'scoring-v1',
    llm: {
      status: llmStatus,
      provider: 'fake',
      model: 'fake-deterministic-v1',
      prompt_version: 'v1',
      error_kind: llmStatus === 'unavailable' ? 'timeout' : null,
    },
    current_state: { monthly_hours: '95.33', monthly_cost: '1763.67' },
    automation_suitability: { process_score: '65.9', policy_version: 'scoring-v1' },
    business_impact: {
      estimated_hours_saved: '5.00',
      estimated_monthly_savings: '92.50',
      monthly_tooling_cost: '50.00',
      net_monthly_savings: '42.50',
      implementation_cost: '3000.00',
      payback_months: '70.59',
      roi_12_months: '-0.83',
      assumptions: { implementation_cost: '3000', monthly_tooling_cost: '50', expected_time_reduction_by_step: { s1: '0.5' } },
      steps_without_reduction: [],
    },
    risks: [{ source: 'AI', type: 'DATA', description: stepName, step_id: 's1' }],
    human_controls: [{ step_id: 's1', step_name: stepName, control: 'REQUIRED', reasons: [stepName] }],
    step_assessments: [
      {
        step_id: 's1',
        position: 1,
        name: stepName,
        monthly_hours: '26.67',
        suitability_score: 68,
        score_factors: [{ name: 'input_type', points: 8, max_points: 15, detail: stepName }],
        score_penalties: [{ name: 'sensitive_data', points: 10 }],
        score_unknowns: [],
        rules_method: 'API_INTEGRATION',
        rules_method_reason: stepName,
        rules_human_control: 'RECOMMENDED',
        human_control_reasons: [stepName],
        ai_suggestion: {
          method: 'AI_CANDIDATE',
          confidence: 0.6,
          interpretation: stepName,
          rationale: stepName,
          human_control_recommended: true,
          dependencies: [stepName],
          risks: [stepName],
          uncertainties: [],
        },
        final_method: 'API_INTEGRATION',
        final_human_control: 'REQUIRED',
        final_source: 'RULES',
        reconciliation_notes: [stepName],
        override: {
          id: 'o1',
          step_id: 's1',
          original_method: 'API_INTEGRATION',
          original_human_control: 'RECOMMENDED',
          new_method: 'MANUAL',
          new_human_control: 'REQUIRED',
          reason: stepName,
          created_at: '2026-10-09T10:00:00Z',
        },
      },
    ],
    architecture_recommendations: [stepName],
    unknowns: [stepName],
  };
}

export function blueprint({ name = 'Invoice intake' } = {}) {
  const a = analysis({ stepName: name });
  return {
    analysis_id: 'a1',
    process_summary: {
      name,
      description: name,
      owner: name,
      executions_per_month: 400,
      steps: 1,
      process_version: 1,
      analysed_at: '2026-10-09T10:00:00+00:00',
      rules_version: 'scoring-v1',
      llm: name,
    },
    current_state: a.current_state,
    automation_opportunities: [
      { position: 1, name, method: 'MANUAL', human_control: 'REQUIRED', decided_by: 'HUMAN', monthly_hours: '26.67', suitability_score: 68, rationale: name },
    ],
    proposed_architecture: [name],
    business_impact: a.business_impact,
    risks: a.risks,
    human_controls: a.human_controls,
    workflow_specification: [name],
  };
}

export const history = () => [
  { id: 'a1', created_at: '2026-10-09T10:00:00Z', process_version: 1, rules_version: 'scoring-v1', llm_status: 'ok', provider: 'fake', model: 'm', override_count: 1 },
];
