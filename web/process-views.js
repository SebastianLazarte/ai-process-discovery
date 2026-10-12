// Processes and steps: the shell, the home page, the step editor, the analysis form and
// the history. Pure functions of API data; app.js owns state and events.

import { h, badge, button, link, empty, section, metric, input, area, select, check, form, table, note } from './views.js';
import { money, number, percent, timestamp, shortId, enumLabel } from './format.js';

export const LEVELS = ['UNKNOWN', 'LOW', 'MEDIUM', 'HIGH'];
export const INPUT_TYPES = ['UNKNOWN', 'DIGITAL_STRUCTURED', 'DIGITAL_UNSTRUCTURED', 'MIXED', 'PHYSICAL'];
export const INTEGRATION = ['UNKNOWN', 'NONE', 'PARTIAL', 'GOOD'];

export function shell(processes, currentId, content) {
  const items = processes.length
    ? processes
        .map(
          p =>
            `<a href="#/processes/${h(p.id)}"${p.id === currentId ? ' aria-current="page"' : ''}><span class="nav-name">${h(p.name)}</span><small>${h(p.step_count)} steps · v${h(p.version)}</small></a>`,
        )
        .join('')
    : '<p class="nav-empty">No processes yet.</p>';
  return `<div class="layout">
<aside class="sidebar">
  <a class="brand" href="#/processes"><img src="icon.svg" alt="">Process Discovery<span>Automation planner</span></a>
  <a class="button primary new" href="#/processes">+ New process</a>
  <nav aria-label="Processes"><h2 class="nav-title">Processes</h2>${items}</nav>
  <p class="sidebar-foot">Deterministic first. The LLM interprets; it never produces a number.</p>
</aside>
<div class="workspace"><main id="main" tabindex="-1">${content}</main></div>
</div>`;
}

export function home(processes, demos) {
  const demoCards = demos
    .map(
      d =>
        `<article class="demo"><h3>${h(d.name)}</h3><p>${h(d.description)}</p>${button('Load demo', 'load-demo', { slug: d.slug }, 'secondary')}</article>`,
    )
    .join('');
  const rows = processes.map(p => [
    `<a href="#/processes/${h(p.id)}"><b>${h(p.name)}</b></a><small>${h(p.owner || 'No owner')}</small>`,
    h(p.executions_per_month),
    h(p.step_count),
    `v${h(p.version)}`,
    h(timestamp(p.updated_at)),
  ]);
  return `<header class="page-heading"><div><p class="eyebrow">AI PROCESS DISCOVERY</p><h1>Map a process.<br>Get numbers you can defend.</h1>
<p>Describe the steps, and the rules engine computes hours, cost, suitability and payback. The LLM only adds interpretation, and it can raise a human control but never remove one.</p></div></header>
${section('Start from a demo', `<div class="demo-grid">${demoCards}</div>`)}
<div class="columns">
${section('New process', processForm())}
${section('Your processes', table(['Process', 'Runs / month', 'Steps', 'Version', 'Updated'], rows, 'No processes yet'))}
</div>`;
}

export function processForm(process = null) {
  const fields =
    input('name', 'Name', { value: process?.name ?? '', required: true }) +
    input('owner', 'Owner', { value: process?.owner ?? '' }) +
    input('executions_per_month', 'Executions per month', { type: 'number', value: process?.executions_per_month ?? 100, required: true }) +
    input('hourly_cost', 'Hourly cost', { type: 'number', value: process?.hourly_cost ?? '', hint: 'Leave empty if unknown. Unknown is not free.' }) +
    area('description', 'Description', process?.description ?? '');
  return process
    ? form('update-process', fields, 'Save process', { process: process.id })
    : form('create-process', fields, 'Create process');
}

const tabs = (process, active, latestAnalysisId) => {
  const tab = (key, title, hash, enabled = true) =>
    enabled
      ? `<a role="tab" href="#${h(hash)}"${key === active ? ' aria-current="page"' : ''}>${h(title)}</a>`
      : `<span role="tab" aria-disabled="true" title="Run an analysis first">${h(title)}</span>`;
  const analysis = latestAnalysisId ? `/analyses/${latestAnalysisId}` : '';
  return `<nav class="tabs" aria-label="Process sections">${tab('steps', 'Steps', `/processes/${process.id}`)}${tab('analyse', 'Analyse', `/processes/${process.id}/analyse`)}${tab('results', 'Results', analysis, Boolean(analysis))}${tab('blueprint', 'Blueprint', `${analysis}/blueprint`, Boolean(analysis))}${tab('history', 'History', `/processes/${process.id}/history`)}</nav>`;
};

export function processHeader(process, active, latestAnalysisId) {
  return `<header class="page-heading"><div><p class="eyebrow">PROCESS · v${h(process.version)}</p><h1>${h(process.name)}</h1>${process.description ? `<p>${h(process.description)}</p>` : ''}</div></header>${tabs(process, active, latestAnalysisId)}`;
}

const stepFlags = step =>
  [
    step.requires_human_judgement && badge('judgement', 'warn', 'Human judgement'),
    step.requires_human_approval && badge('approval', 'warn', 'Approval'),
    step.handles_sensitive_data && badge('sensitive', 'bad', 'Sensitive data'),
  ]
    .filter(Boolean)
    .join('');

export function stepsPage(process) {
  const steps = process.steps;
  const rows = steps
    .map(
      (step, i) => `<article class="step">
  <span class="step-pos">${h(String(step.position).padStart(2, '0'))}</span>
  <div class="step-body">
    <h3>${h(step.name)}</h3>
    <p>${h(step.responsible_role || 'No role')} · ${h(number(step.minutes_per_execution, 1))} min · runs in ${h(percent(step.occurrence_rate))} of executions</p>
    <div class="tags">${badge(step.input_type, '', enumLabel(step.input_type))}${badge(step.integration_readiness, '', `Integration: ${enumLabel(step.integration_readiness)}`)}${badge(step.rule_clarity, '', `Rules: ${enumLabel(step.rule_clarity)}`)}${stepFlags(step)}</div>
  </div>
  <div class="step-actions">
    ${button('↑', 'move-step', { process: process.id, step: step.id, delta: -1 }, 'quiet', { label: `Move ${step.name} up`, disabled: i === 0 })}
    ${button('↓', 'move-step', { process: process.id, step: step.id, delta: 1 }, 'quiet', { label: `Move ${step.name} down`, disabled: i === steps.length - 1 })}
    ${button('Edit', 'edit-step', { process: process.id, step: step.id })}
    ${button('Delete', 'delete-step', { process: process.id, step: step.id }, 'secondary danger')}
  </div>
</article>`,
    )
    .join('');
  return `<div class="metrics">
${metric('Executions / month', number(process.executions_per_month, 0))}
${metric('Hourly cost', money(process.hourly_cost), process.hourly_cost === null ? 'Costs stay unknown' : '')}
${metric('Steps', String(steps.length))}
${metric('Owner', process.owner || 'None')}
</div>
${section(
  'Steps',
  steps.length ? `<div class="steps">${rows}</div>` : empty('No steps yet', 'Add the first step to analyse this process.'),
  `<div class="actions">${button('Add step', 'add-step', { process: process.id }, 'primary')}</div>`,
)}
${section('Process settings', processForm(process), button('Delete process', 'delete-process', { process: process.id }, 'secondary danger'))}`;
}

export function stepForm(processId, step = null) {
  const s = step ?? {};
  const fields =
    input('name', 'Name', { value: s.name ?? '', required: true }) +
    input('responsible_role', 'Responsible role', { value: s.responsible_role ?? '' }) +
    area('description', 'Description', s.description ?? '') +
    input('minutes_per_execution', 'Minutes per execution', { type: 'number', value: s.minutes_per_execution ?? '5', required: true }) +
    input('occurrence_rate', 'Occurrence rate (0 to 1)', { type: 'number', value: s.occurrence_rate ?? '1', hint: 'Share of executions that go through this step.' }) +
    input('exception_rate', 'Exception rate (0 to 1)', { type: 'number', value: s.exception_rate ?? '', hint: 'Leave empty if unknown.' }) +
    select('repetitiveness', 'Repetitiveness', LEVELS, s.repetitiveness ?? 'UNKNOWN') +
    select('rule_clarity', 'Rule clarity', LEVELS, s.rule_clarity ?? 'UNKNOWN') +
    select('criticality', 'Criticality', LEVELS, s.criticality ?? 'UNKNOWN') +
    select('input_type', 'Input type', INPUT_TYPES, s.input_type ?? 'UNKNOWN') +
    select('integration_readiness', 'Integration readiness', INTEGRATION, s.integration_readiness ?? 'UNKNOWN') +
    input('tools', 'Tools', { value: (s.tools ?? []).join(', '), hint: 'Comma separated.' }) +
    `<fieldset class="wide flags"><legend>Controls and data</legend>${check('requires_human_judgement', 'Requires human judgement', s.requires_human_judgement)}${check('requires_human_approval', 'Requires human approval', s.requires_human_approval)}${check('handles_sensitive_data', 'Handles sensitive data', s.handles_sensitive_data)}</fieldset>`;
  return `<h2>${step ? `Edit step ${h(step.position)}` : 'Add a step'}</h2>${form('save-step', fields, step ? 'Save step' : 'Add step', step ? { process: processId, step: step.id } : { process: processId })}`;
}

export const sensitiveSteps = process => process.steps.filter(s => s.handles_sensitive_data).map(s => s.name);

export const canRunAnalysis = (process, useLlm, confirmed) =>
  process.steps.length > 0 && (!useLlm || confirmed || sensitiveSteps(process).length === 0);

export function analysePage(process, { useLlm = false, confirmed = false } = {}) {
  if (!process.steps.length) return section('Analyse', empty('No steps to analyse', 'Add steps on the Steps tab first.'));
  const sensitive = sensitiveSteps(process);
  const reductions = process.steps
    .map(
      step => `<label class="range wide">${h(step.position)}. ${h(step.name)}
  <span class="range-row"><input type="range" name="reduction:${h(step.id)}" min="0" max="1" step="0.05" value="0" data-output="out-${h(step.id)}"><output id="out-${h(step.id)}">${h(percent(0))}</output></span></label>`,
    )
    .join('');
  const warning = sensitive.length
      ? `<div class="wide" data-sensitive-warning${useLlm ? '' : ' hidden'}>${note(`These steps handle sensitive data and their descriptions would be sent to the LLM provider: ${sensitive.join(', ')}.`, 'bad')}${check('confirm_sensitive', 'I confirm these descriptions can be sent to the provider', confirmed, 'wide')}</div>`
      : '';
  const fields = `<p class="wide lead">Economic inputs are your assumptions. The system never estimates them and the LLM never sees them.</p>
${input('implementation_cost', 'Implementation cost', { type: 'number', hint: 'Leave empty if unknown.' })}
${input('monthly_tooling_cost', 'Monthly tooling cost', { type: 'number', value: '0' })}
<fieldset class="wide"><legend>Expected time reduction per step</legend>${reductions}</fieldset>
${check('use_llm', 'Enrich with the LLM: interpretation, risks and architecture', useLlm, 'wide')}
${warning}`;
  return section(
    'Analyse',
    form('run-analysis', fields, 'Run analysis', { process: process.id }, { disabled: !canRunAnalysis(process, useLlm, confirmed) }),
  );
}

export function historyPage(process, rows) {
  const lines = rows.map(row => [
    h(timestamp(row.created_at)),
    `<code>${h(shortId(row.id))}</code>`,
    `v${h(row.process_version)}`,
    h(row.rules_version),
    badge(row.llm_status, undefined, row.llm_status === 'not_requested' ? 'Not requested' : enumLabel(row.llm_status)),
    h(row.override_count),
    link('Open', `/analyses/${row.id}`),
  ]);
  return section(
    'Analysis history',
    `<p>Each analysis is an immutable snapshot. Results differ when the process version, the rules version or the LLM changed.</p>${table(['Created', 'Id', 'Process', 'Rules', 'LLM', 'Overrides', ''], lines, 'No analyses yet')}`,
  );
}
