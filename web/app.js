// Orchestration: hash routing, state, and event delegation. Views are pure functions in
// the *-views.js modules; this file wires them to the API and the DOM.
//
// Numbers typed into forms travel to the API as strings and the API validates and
// converts them. The client never parses or computes a figure (RS-50).

import { call, ApiError } from './api.js';
import { h, section } from './views.js';
import { percent, shortId } from './format.js';
import * as pv from './process-views.js';
import * as av from './analysis-views.js';

const root = document.querySelector('#root');
const dialog = document.querySelector('#dialog');
const dialogBody = document.querySelector('#dialog-body');
let renderVersion = 0;
let current = { process: null, analysis: null };

function toast(message, error = false) {
  const el = document.querySelector('#toast');
  el.textContent = message;
  el.className = `show${error ? ' error' : ''}`;
  clearTimeout(toast.timer);
  toast.timer = setTimeout(() => (el.className = ''), 6000);
}

function openDialog(html) {
  dialogBody.innerHTML = html;
  if (!dialog.open) dialog.showModal();
  dialogBody.querySelector('input, select, textarea')?.focus();
}

function closeDialog() {
  if (dialog.open) dialog.close();
}

function parseRoute() {
  const [kind, id, sub] = location.hash.replace(/^#\/?/, '').split('/');
  if (kind === 'processes' && id) return { page: sub || 'steps', processId: id };
  if (kind === 'analyses' && id) return { page: sub === 'blueprint' ? 'blueprint' : 'results', analysisId: id };
  return { page: 'home' };
}

const PAGES = {
  steps: ({ process }) => pv.stepsPage(process),
  analyse: ({ process }) => pv.analysePage(process),
  history: ({ process, history }) => pv.historyPage(process, history),
  results: ({ process, analysis }) => av.resultsPage(analysis, process),
  blueprint: ({ process, blueprint }) => av.blueprintPage(blueprint, process),
};

// Asked once per page load. Without an answer the client runs as before, with no banner.
const metaRequest = call('getMeta').catch(() => null);

async function render({ focus = false, open = null } = {}) {
  const version = ++renderVersion;
  const route = parseRoute();
  let processes = [];
  let processId = route.processId ?? null;
  let content;
  try {
    processes = await call('listProcesses');
    if (route.page === 'home') {
      content = pv.home(processes, await call('listDemos'));
      current = { process: null, analysis: null };
    } else {
      const page = PAGES[route.page];
      if (!page) throw new ApiError(404, 'This page does not exist.');
      let analysis = null;
      let blueprint = null;
      if (route.analysisId) {
        [analysis, blueprint] = await Promise.all([
          call('getAnalysis', { analysis_id: route.analysisId }),
          route.page === 'blueprint' ? call('getBlueprint', { analysis_id: route.analysisId }) : null,
        ]);
        processId = analysis.process_id;
      }
      const [process, history] = await Promise.all([
        call('getProcess', { process_id: processId }),
        call('listAnalyses', { process_id: processId }),
      ]);
      current = { process, analysis };
      const latest = analysis?.id ?? history[0]?.id;
      content = pv.processHeader(process, route.page, latest) + page({ process, history, analysis, blueprint });
    }
  } catch (error) {
    content = section(
      error.status === 404 ? 'Not found' : 'Something went wrong',
      `<p>${h(error.message)}</p><a class="button" href="#/processes">Back to processes</a>`,
    );
  }
  if (version !== renderVersion) return;
  root.innerHTML = pv.shell(processes, processId, content, await metaRequest);
  if (open) document.getElementById(open)?.setAttribute('open', '');
  if (focus) {
    window.scrollTo(0, 0);
    document.querySelector('#main')?.focus({ preventScroll: true });
  }
}

// Form payloads. Empty optional fields become null ("unknown"), never zero.

const text = (data, name) => String(data.get(name) ?? '').trim();
const optional = (data, name) => text(data, name) || null;

function processPayload(data) {
  return {
    name: text(data, 'name'),
    owner: optional(data, 'owner'),
    description: text(data, 'description'),
    executions_per_month: text(data, 'executions_per_month'),
    hourly_cost: optional(data, 'hourly_cost'),
  };
}

function stepPayload(data) {
  return {
    name: text(data, 'name'),
    responsible_role: text(data, 'responsible_role'),
    description: text(data, 'description'),
    minutes_per_execution: text(data, 'minutes_per_execution'),
    occurrence_rate: text(data, 'occurrence_rate') || '1',
    exception_rate: optional(data, 'exception_rate'),
    repetitiveness: text(data, 'repetitiveness'),
    rule_clarity: text(data, 'rule_clarity'),
    criticality: text(data, 'criticality'),
    input_type: text(data, 'input_type'),
    integration_readiness: text(data, 'integration_readiness'),
    tools: text(data, 'tools').split(',').map(t => t.trim()).filter(Boolean),
    requires_human_judgement: data.has('requires_human_judgement'),
    requires_human_approval: data.has('requires_human_approval'),
    handles_sensitive_data: data.has('handles_sensitive_data'),
  };
}

function analysisPayload(data) {
  const reductions = {};
  for (const [name, value] of data.entries()) {
    if (name.startsWith('reduction:') && value !== '0') reductions[name.slice('reduction:'.length)] = value;
  }
  return {
    use_llm: data.has('use_llm'),
    confirm_sensitive: data.has('confirm_sensitive'),
    assumptions: {
      implementation_cost: optional(data, 'implementation_cost'),
      monthly_tooling_cost: text(data, 'monthly_tooling_cost') || '0',
      expected_time_reduction_by_step: reductions,
    },
  };
}

const FORMS = {
  'create-process': async (data) => {
    const created = await call('createProcess', {}, processPayload(data));
    location.hash = `#/processes/${created.id}`;
  },
  'update-process': async (data, form) => {
    await call('updateProcess', { process_id: form.dataset.process }, processPayload(data));
    toast('Process saved.');
    await render();
  },
  'save-step': async (data, form) => {
    const payload = stepPayload(data);
    if (form.dataset.step) await call('updateStep', { step_id: form.dataset.step }, payload);
    else await call('addStep', { process_id: form.dataset.process }, payload);
    closeDialog();
    toast(form.dataset.step ? 'Step saved.' : 'Step added.');
    await render();
  },
  'run-analysis': async (data, form) => {
    const analysis = await call('runAnalysis', { process_id: form.dataset.process }, analysisPayload(data));
    toast(analysis.llm.status === 'unavailable' ? 'Saved without the LLM: it was unavailable.' : 'Analysis saved.');
    location.hash = `#/analyses/${analysis.id}`;
  },
  override: async (data, form) => {
    await call('addOverride', { analysis_id: form.dataset.analysis }, {
      step_id: form.dataset.step,
      method: text(data, 'method'),
      human_control: text(data, 'human_control'),
      reason: text(data, 'reason'),
    });
    toast('Override saved. The original recommendation is kept.');
    await render({ open: `assessment-${form.dataset.step}` });
  },
};

// Maps an API field path to the form control that produced it.
function controlFor(form, field) {
  const parts = field.split('.');
  const reduction = parts.indexOf('expected_time_reduction_by_step');
  const name = reduction >= 0 ? `reduction:${parts[reduction + 1]}` : parts.at(-1);
  return form.elements.namedItem(field) ?? form.elements.namedItem(name);
}

function showFormError(form, error) {
  form.querySelectorAll('.field-error').forEach(el => el.remove());
  form.querySelectorAll('[aria-invalid]').forEach(el => el.removeAttribute('aria-invalid'));
  const unmatched = [];
  for (const [field, message] of Object.entries(error.fields ?? {})) {
    const control = controlFor(form, field);
    if (control?.insertAdjacentHTML) {
      control.setAttribute('aria-invalid', 'true');
      control.insertAdjacentHTML('afterend', `<small class="field-error">${h(message)}</small>`);
    } else {
      unmatched.push(`${field}: ${message}`);
    }
  }
  form.querySelector('.form-error').textContent = [error.message, ...unmatched].join('\n');
  form.querySelector('[aria-invalid]')?.focus();
}

document.addEventListener('submit', async event => {
  const form = event.target.closest('form[data-action]');
  if (!form) return;
  event.preventDefault();
  const submit = form.querySelector('button[type=submit]');
  submit.disabled = true;
  try {
    await FORMS[form.dataset.action](new FormData(form), form);
  } catch (error) {
    if (!(error instanceof ApiError)) throw error;
    showFormError(form, error);
    if (error.status === 409) toast(error.message, true);
  } finally {
    if (form.isConnected) submit.disabled = false;
  }
});

const ACTIONS = {
  'close-dialog': () => closeDialog(),
  'load-demo': async el => {
    const created = await call('loadDemo', { slug: el.dataset.slug });
    toast(`Loaded "${created.name}".`);
    location.hash = `#/processes/${created.id}`;
  },
  'add-step': el => openDialog(pv.stepForm(el.dataset.process)),
  'edit-step': el => openDialog(pv.stepForm(el.dataset.process, current.process.steps.find(s => s.id === el.dataset.step))),
  'delete-step': async el => {
    const step = current.process.steps.find(s => s.id === el.dataset.step);
    if (!confirm(`Delete step "${step.name}"?`)) return;
    await call('deleteStep', { step_id: step.id });
    toast('Step deleted.');
    await render();
  },
  'move-step': async el => {
    const ids = current.process.steps.map(s => s.id);
    const from = ids.indexOf(el.dataset.step);
    const to = from + (el.dataset.delta === '1' ? 1 : -1);
    if (to < 0 || to >= ids.length) return;
    [ids[from], ids[to]] = [ids[to], ids[from]];
    await call('reorderSteps', { process_id: el.dataset.process }, { step_ids: ids });
    await render();
  },
  'delete-process': async el => {
    if (!confirm(`Delete "${current.process.name}" and all its analyses?`)) return;
    await call('deleteProcess', { process_id: el.dataset.process });
    toast('Process deleted.');
    location.hash = '#/processes';
  },
  'download-blueprint': async el => {
    const markdown = await call('getBlueprintMarkdown', { analysis_id: el.dataset.analysis });
    const url = URL.createObjectURL(new Blob([markdown], { type: 'text/markdown' }));
    const anchor = Object.assign(document.createElement('a'), { href: url, download: `blueprint-${shortId(el.dataset.analysis)}.md` });
    anchor.click();
    URL.revokeObjectURL(url);
  },
};

document.addEventListener('click', async event => {
  const el = event.target.closest('button[data-action]');
  if (!el || !ACTIONS[el.dataset.action]) return;
  el.disabled = true;
  try {
    await ACTIONS[el.dataset.action](el);
  } catch (error) {
    if (!(error instanceof ApiError)) throw error;
    toast(error.message, true);
  } finally {
    if (el.isConnected) el.disabled = false;
  }
});

// Live behaviour of the analysis form: slider labels and the sensitive-data gate (RS-54).
document.addEventListener('input', event => {
  const el = event.target;
  if (el.type === 'range' && el.dataset.output) {
    document.getElementById(el.dataset.output).textContent = percent(el.value);
  }
  const form = el.closest('form[data-action="run-analysis"]');
  if (!form || !['use_llm', 'confirm_sensitive'].includes(el.name)) return;
  const useLlm = form.elements.namedItem('use_llm').checked;
  const confirmed = form.elements.namedItem('confirm_sensitive')?.checked ?? false;
  form.querySelector('[data-sensitive-warning]')?.toggleAttribute('hidden', !useLlm);
  form.querySelector('button[type=submit]').disabled = !pv.canRunAnalysis(current.process, useLlm, confirmed);
});

window.addEventListener('hashchange', () => {
  closeDialog();
  render({ focus: true });
});

if (!location.hash) history.replaceState(null, '', '#/processes');
render();
