// RS-50: the client prints the API's figures and never invents one.
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { money, hours, months, percent, score, enumLabel, detail, timestamp } from '../format.js';

test('money prints API strings with two decimals and grouping', () => {
  assert.equal(money('493.33'), '493.33');
  assert.equal(money('1763.67'), '1,763.67');
});

test('unknown is never shown as zero', () => {
  for (const format of [money, hours]) {
    assert.equal(format(null), 'unknown');
    assert.equal(format(undefined), 'unknown');
  }
  assert.equal(months(null), 'n/a');
  assert.equal(percent(null), 'n/a');
  assert.equal(score(null), 'n/a');
});

test('ratios are printed as percentages', () => {
  assert.equal(percent('2.80'), '280%');
  assert.equal(percent('-0.83'), '-83%');
  assert.equal(percent('0.05'), '5%');
});

test('enum labels read as words and keep acronyms', () => {
  assert.equal(enumLabel('DIGITAL_STRUCTURED'), 'Digital structured');
  assert.equal(enumLabel('API_INTEGRATION'), 'API integration');
  assert.equal(enumLabel('AI_CANDIDATE'), 'AI candidate');
  assert.equal(enumLabel('AI'), 'AI');
});

test('details translate raw enums and leave prose alone', () => {
  assert.equal(detail('DIGITAL_UNSTRUCTURED'), 'Digital unstructured');
  assert.equal(detail('0.02 of executions'), '0.02 of executions');
});

test('timestamps keep date and minutes in UTC', () => {
  assert.equal(timestamp('2026-10-09T15:30:33.688840Z'), '2026-10-09 15:30 UTC');
});
