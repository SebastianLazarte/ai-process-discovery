// Analysis results and blueprint. Suitability, business impact, risk and human controls
// stay in four separate panels and nothing combines them into one score (RS-53).

import { h, badge, button, empty, section, metric, select, input, form, table, list, note, meter } from './views.js';
import { money, number, hours, months, percent, score, timestamp, shortId, enumLabel, detail } from './format.js';

export const METHODS = ['RULE_BASED', 'API_INTEGRATION', 'AI_CANDIDATE', 'HYBRID', 'MANUAL', 'NEEDS_REVIEW'];
export const CONTROLS = ['NONE', 'RECOMMENDED', 'REQUIRED'];

const llmLabel = llm =>
  llm.status === 'not_requested' ? 'LLM not requested' : `LLM ${llm.status}${llm.model ? ` · ${llm.provider}/${llm.model}` : ''}`;

export function provenance(analysis) {
  const llm = analysis.llm;
  return `<p class="provenance">Analysis <code>${h(shortId(analysis.id))}</code> · ${h(timestamp(analysis.created_at))} · process v${h(analysis.process_version)} · rules ${h(analysis.rules_version)} · ${badge(llm.status, undefined, llmLabel(llm))}${llm.prompt_version ? ` · prompt ${h(llm.prompt_version)}` : ''}</p>`;
}

function suitabilityPanel(analysis) {
  const suit = analysis.automation_suitability;
  const steps = analysis.step_assessments
    .map(
      s =>
        `<li><span>${h(s.position)}. ${h(s.name)}</span>${meter(s.suitability_score, `${s.name} suitability`)}<b>${h(s.suitability_score)}</b></li>`,
    )
    .join('');
  return section(
    'Automation suitability',
    `<p class="big">${h(score(suit.process_score))}<small> / 100</small></p>
<p>Whether a step can be automated, weighted by the time it takes. It says nothing about whether it is worth it.</p>
<ul class="bars">${steps}</ul>`,
    `<small>${h(suit.policy_version)}</small>`,
    'quad',
  );
}

function impactPanel(analysis, stepNames) {
  const b = analysis.business_impact;
  const missing = b.steps_without_reduction.map(id => stepNames[id] ?? shortId(id));
  return section(
    'Business impact',
    `<div class="mini-metrics">
${metric('Hours freed / month', hours(b.estimated_hours_saved))}
${metric('Net savings / month', money(b.net_monthly_savings))}
${metric('Payback', months(b.payback_months))}
${metric('Gross savings / month', money(b.estimated_monthly_savings))}
${metric('Implementation cost', money(b.implementation_cost))}
${metric('ROI at 12 months', percent(b.roi_12_months))}
</div>
${missing.length ? note(`No expected reduction given for ${missing.join(', ')}. They count as zero.`, 'info') : ''}
<p>Computed from your assumptions only. An unknown hourly cost leaves savings, payback and ROI unknown.</p>`,
    '',
    'quad',
  );
}

function riskPanel(analysis) {
  const risks = (analysis.risks ?? []).map(r => `${badge(r.source)} <b>${h(enumLabel(r.type))}</b>: ${h(r.description)}`);
  return section(
    'Risk',
    `${list(risks, 'No risks flagged.')}${analysis.unknowns.length ? `<h3>Unknowns</h3>${list(analysis.unknowns.map(h))}` : ''}`,
    '',
    'quad',
  );
}

function controlsPanel(analysis) {
  const controls = (analysis.human_controls ?? []).map(
    c => `${badge(c.control)} <b>${h(c.step_name)}</b>: ${h(c.reasons.join('; '))}`,
  );
  return section(
    'Human controls',
    `${list(controls, 'No human control required by the rules.')}<p>The LLM can raise a control and never lower one.</p>`,
    '',
    'quad',
  );
}

function rulesColumn(step) {
  const factors = table(
    ['Factor', 'Points', 'Detail'],
    step.score_factors.map(f => [h(enumLabel(f.name)), `${h(f.points)} / ${h(f.max_points)}`, h(detail(f.detail))]),
  );
  const penalties = step.score_penalties.length
    ? `<p><b>Penalties:</b> ${h(step.score_penalties.map(p => `${enumLabel(p.name)} (-${p.points})`).join(', '))}</p>`
    : '';
  const unknowns = step.score_unknowns.length ? `<p><b>Unknown inputs:</b> ${h(step.score_unknowns.map(enumLabel).join(', '))}</p>` : '';
  return `<div><h4>Rules</h4><p>${badge(step.rules_method)} ${h(step.rules_method_reason)}</p>${factors}${penalties}${unknowns}</div>`;
}

function aiColumn(step) {
  const ai = step.ai_suggestion;
  const notes = step.reconciliation_notes.map(n => `<p class="small">Reconciliation: ${h(n)}</p>`).join('');
  const override = step.override
    ? note(`Overridden from ${enumLabel(step.override.original_method)} / ${enumLabel(step.override.original_human_control)}: ${step.override.reason}`, 'info')
    : '';
  if (!ai) return `<div><h4>AI suggestion</h4><p>No AI suggestion for this analysis.</p>${notes}${override}</div>`;
  const extras = [
    ['Dependencies', ai.dependencies],
    ['Risks', ai.risks],
    ['Uncertainties', ai.uncertainties],
  ]
    .filter(([, items]) => items.length)
    .map(([title, items]) => `<p><b>${h(title)}:</b> ${h(items.join('; '))}</p>`)
    .join('');
  return `<div><h4>AI suggestion</h4><p>${badge(ai.method)} confidence ${h(percent(ai.confidence))}</p><p>${h(ai.interpretation)}</p><p class="small">${h(ai.rationale)}</p>${extras}${notes}${override}</div>`;
}

function overrideForm(analysis, step) {
  const fields =
    select('method', 'Method', METHODS, step.final_method) +
    select('human_control', 'Human control', CONTROLS, step.final_human_control) +
    input('reason', 'Reason', { required: true, attrs: 'minlength="3"' });
  return `<div class="override"><h4>Override this recommendation</h4>${form('override', fields, 'Save override', { analysis: analysis.id, step: step.step_id })}</div>`;
}

function stepDetail(analysis, step) {
  return `<details class="assessment" id="assessment-${h(step.step_id)}">
<summary><span class="step-pos">${h(String(step.position).padStart(2, '0'))}</span><span class="assessment-name">${h(step.name)}</span><span class="tags">${badge(step.final_method)}${badge(step.final_human_control, undefined, `Control: ${enumLabel(step.final_human_control)}`)}${badge(step.final_source, undefined, `By ${enumLabel(step.final_source)}`)}</span><span class="assessment-hours">${h(hours(step.monthly_hours))}</span></summary>
<div class="assessment-body">${rulesColumn(step)}${aiColumn(step)}</div>
${overrideForm(analysis, step)}
</details>`;
}

export function resultsPage(analysis, process) {
  const stepNames = Object.fromEntries((process?.steps ?? []).map(s => [s.id, s.name]));
  const unavailable =
    analysis.llm.status === 'unavailable'
      ? note(`The LLM was unavailable (${analysis.llm.error_kind ?? 'error'}). Deterministic results are complete.`, 'warn')
      : '';
  return `${provenance(analysis)}${unavailable}
<div class="metrics two">
${metric('Current monthly hours', hours(analysis.current_state.monthly_hours))}
${metric('Current monthly cost', money(analysis.current_state.monthly_cost))}
</div>
<div class="quads">${suitabilityPanel(analysis)}${impactPanel(analysis, stepNames)}${riskPanel(analysis)}${controlsPanel(analysis)}</div>
${section('Step by step', analysis.step_assessments.map(step => stepDetail(analysis, step)).join(''), '<small>Open a step to see the rules, the AI suggestion and to override it.</small>')}`;
}

export function blueprintPage(blueprint, process) {
  const stepNames = Object.fromEntries((process?.steps ?? []).map(s => [s.id, s.name]));
  const summary = blueprint.process_summary;
  const summaryRows = [
    ['Owner', summary.owner || 'None'],
    ['Executions per month', summary.executions_per_month],
    ['Steps', summary.steps],
    ['Process version', `v${summary.process_version}`],
    ['Analysed', timestamp(summary.analysed_at)],
    ['Rules', summary.rules_version],
    ['LLM', summary.llm],
  ]
    .map(([k, v]) => `<dt>${h(k)}</dt><dd>${h(v)}</dd>`)
    .join('');
  const impact = blueprint.business_impact;
  const reductions = Object.entries(impact.assumptions.expected_time_reduction_by_step).map(
    ([id, value]) => `${h(stepNames[id] ?? shortId(id))}: ${h(percent(value))}`,
  );
  const opportunities = table(
    ['#', 'Step', 'Method', 'Control', 'Decided by', 'Hours / month', 'Score', 'Rationale'],
    blueprint.automation_opportunities.map(o => [
      h(o.position),
      `<b>${h(o.name)}</b>`,
      badge(o.method),
      badge(o.human_control),
      h(enumLabel(o.decided_by)),
      h(number(o.monthly_hours)),
      h(o.suitability_score),
      h(o.rationale),
    ]),
  );
  return `<div class="blueprint-head"><p>Eight sections, built from the analysis with every override applied.</p>${button('Download .md', 'download-blueprint', { analysis: blueprint.analysis_id }, 'primary')}</div>
${section('1. Process summary', `${summary.description ? `<p>${h(summary.description)}</p>` : ''}<dl class="facts">${summaryRows}</dl>`)}
${section('2. Current state', `<div class="metrics two">${metric('Monthly hours', hours(blueprint.current_state.monthly_hours))}${metric('Monthly cost', money(blueprint.current_state.monthly_cost))}</div>`)}
${section('3. Automation opportunities', opportunities, '<small>Ordered by monthly hours</small>')}
${section('4. Proposed architecture', list(blueprint.proposed_architecture.map(h), 'No architecture proposed.'))}
${section(
  '5. Business impact',
  `<div class="mini-metrics">${metric('Hours freed / month', hours(impact.estimated_hours_saved))}${metric('Net savings / month', money(impact.net_monthly_savings))}${metric('Payback', months(impact.payback_months))}${metric('ROI at 12 months', percent(impact.roi_12_months))}</div>
<h3>Assumptions</h3>${list([
    `Implementation cost: ${h(money(impact.assumptions.implementation_cost))}`,
    `Monthly tooling cost: ${h(money(impact.assumptions.monthly_tooling_cost))}`,
    ...reductions.map(r => `Expected time reduction, ${r}`),
  ])}`,
)}
${section('6. Risks', list(blueprint.risks.map(r => `${badge(r.source)} ${h(r.description)}`), 'No risks flagged.'))}
${section('7. Human controls', list(blueprint.human_controls.map(c => `${badge(c.control)} <b>${h(c.step_name)}</b>: ${h(c.reasons.join('; '))}`), 'No human control required.'))}
${section('8. Workflow specification', blueprint.workflow_specification.length ? `<ol class="workflow">${blueprint.workflow_specification.map(line => `<li>${h(line)}</li>`).join('')}</ol>` : empty('No workflow'))}`;
}
