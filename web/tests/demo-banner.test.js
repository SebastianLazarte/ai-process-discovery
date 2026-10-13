// RS-62: the public demo banner appears only when the API says so, and escapes its input.
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { demoBanner, shell } from '../process-views.js';

test('the banner shows only for a public demo', () => {
  assert.equal(demoBanner(null), '');
  assert.equal(demoBanner({ version: '1.2.0', public_demo: false }), '');
  const html = demoBanner({ version: '1.2.0', public_demo: true });
  assert.ok(html.includes('Public demo v1.2.0'));
  assert.ok(html.includes('Do not enter real or personal data'));
});

test('the banner sits above the main content and escapes the version', () => {
  const html = shell([], null, '<p>content</p>', { version: '<b>x</b>', public_demo: true });
  assert.ok(html.indexOf('demo-banner') < html.indexOf('id="main"'));
  assert.ok(html.includes('&lt;b&gt;x&lt;/b&gt;'));
  assert.ok(!shell([], null, '').includes('demo-banner'));
});
