// RS-49 and RS-56: endpoint templates and error mapping.
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { ENDPOINTS, fillPath, describeError } from '../api.js';

test('path parameters are filled and encoded', () => {
  assert.equal(fillPath(ENDPOINTS.getProcess[1], { process_id: 'a/b' }), '/processes/a%2Fb');
  assert.throws(() => fillPath(ENDPOINTS.getProcess[1], {}), /process_id/);
});

test('request validation errors map to form fields', () => {
  const result = describeError(422, {
    detail: [{ loc: ['body', 'occurrence_rate'], msg: 'Input should be less than or equal to 1' }],
  });
  assert.equal(result.message, 'Check the highlighted fields.');
  assert.deepEqual(result.fields, { occurrence_rate: 'Input should be less than or equal to 1' });
});

test('nested validation paths keep their dots', () => {
  const result = describeError(422, {
    detail: [{ loc: ['body', 'assumptions', 'implementation_cost'], msg: 'bad' }],
  });
  assert.deepEqual(result.fields, { 'assumptions.implementation_cost': 'bad' });
});

test('domain errors carry their field', () => {
  const result = describeError(422, { detail: 'exception rate must be between 0 and 1', field: 'exception_rate' });
  assert.deepEqual(result.fields, { exception_rate: 'exception rate must be between 0 and 1' });
});

test('conflicts keep the server message', () => {
  const result = describeError(409, { detail: 'Resend with confirm_sensitive=true', code: 'sensitive_data_confirmation_required' });
  assert.equal(result.message, 'Resend with confirm_sensitive=true');
  assert.deepEqual(result.fields, {});
});

test('empty bodies still produce a message', () => {
  assert.equal(describeError(500, null).message, 'Request failed (500).');
});
