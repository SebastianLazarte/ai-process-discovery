// RS-51, RS-53, RS-54 and RS-58: escaping, four separate panels, the sensitive-data gate
// and unknown option values.
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { shell, home, stepsPage, stepForm, analysePage, historyPage, processHeader, canRunAnalysis } from '../process-views.js';
import { resultsPage, blueprintPage } from '../analysis-views.js';
import { select } from '../views.js';
import { process, analysis, blueprint, history } from './fixtures.js';

const EVIL = '<img src=x onerror=alert(1)>';

test('every view escapes user text', () => {
  const p = process({ name: EVIL, description: EVIL, owner: EVIL, stepName: EVIL, sensitive: true });
  const pages = [
    shell([{ id: 'p1', name: EVIL, step_count: 1, version: 1 }], 'p1', ''),
    home(
      [{ id: 'p1', name: EVIL, owner: EVIL, executions_per_month: 1, step_count: 1, version: 1, updated_at: '' }],
      [{ slug: 's', name: EVIL, description: EVIL }],
    ),
    processHeader(p, 'steps', null),
    stepsPage(p),
    stepForm(p.id, p.steps[0]),
    analysePage(p, { useLlm: true }),
    resultsPage(analysis({ stepName: EVIL }), p),
    blueprintPage(blueprint({ name: EVIL }), p),
  ];
  for (const html of pages) {
    assert.ok(!html.includes('<img src=x'), html.slice(0, 200));
    assert.ok(html.includes('&lt;img src=x'), html.slice(0, 200));
  }
  assert.ok(!historyPage(p, history()).includes('<img'));
});

test('results show four separate panels and no combined score', () => {
  const html = resultsPage(analysis(), process());
  for (const title of ['Automation suitability', 'Business impact', 'Risk', 'Human controls']) {
    assert.ok(html.includes(`<h2>${title}</h2>`), title);
  }
  assert.equal((html.match(/class="panel quad"/g) || []).length, 4);
  assert.ok(!/overall|combined score/i.test(html));
});

test('an unavailable LLM is announced and deterministic results stay', () => {
  const html = resultsPage(analysis({ llmStatus: 'unavailable' }), process());
  assert.ok(html.includes('The LLM was unavailable'));
  assert.ok(html.includes('95.33 h'));
});

test('analysis with the LLM needs confirmation when a step is sensitive', () => {
  const sensitive = process({ sensitive: true });
  assert.equal(canRunAnalysis(sensitive, false, false), true);
  assert.equal(canRunAnalysis(sensitive, true, false), false);
  assert.equal(canRunAnalysis(sensitive, true, true), true);
  assert.equal(canRunAnalysis(process(), true, false), true);
  assert.ok(analysePage(sensitive, { useLlm: true }).includes('type="submit" disabled'));
  assert.ok(!analysePage(sensitive, { useLlm: false }).includes('type="submit" disabled'));
});

test('select keeps an unknown current value selected', () => {
  const html = select('human_control', 'Human control', ['NONE', 'REQUIRED'], 'SUPERVISED');
  assert.ok(html.includes('<option value="SUPERVISED" selected>'));
  assert.ok(!/<option value="NONE" selected>/.test(html));
  assert.equal((select('c', 'C', ['NONE', 'REQUIRED'], 'REQUIRED').match(/<option/g) || []).length, 2);
});

test('a process without steps cannot be analysed', () => {
  assert.equal(canRunAnalysis(process({ steps: 0 }), false, false), false);
});
