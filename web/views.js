// View primitives. Every function returns an HTML string and every value it interpolates
// goes through h() (RS-51). The CSP forbids inline scripts and inline styles, so markup
// carries data-action attributes and classes only.

import { enumLabel } from './format.js';

export const h = value =>
  String(value ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[c]);

const TONES = {
  good: ['RULE_BASED', 'API_INTEGRATION', 'NONE', 'ok'],
  info: ['AI_CANDIDATE', 'HYBRID', 'AI', 'RULES'],
  warn: ['RECOMMENDED', 'NEEDS_REVIEW', 'unavailable', 'HUMAN'],
  bad: ['REQUIRED', 'MANUAL'],
};

export const toneOf = value => Object.keys(TONES).find(tone => TONES[tone].includes(value)) || '';

export const badge = (value, tone = toneOf(value), text = enumLabel(value)) =>
  `<span class="badge ${h(tone)}">${h(text)}</span>`;

export const button = (title, action, attrs = {}, kind = 'secondary', { disabled = false, label = '' } = {}) =>
  `<button type="button" class="${h(kind)}" data-action="${h(action)}"${dataAttrs(attrs)}${label ? ` aria-label="${h(label)}"` : ''}${disabled ? ' disabled' : ''}>${h(title)}</button>`;

export const link = (title, hash, kind = 'secondary') => `<a class="button ${h(kind)}" href="#${h(hash)}">${h(title)}</a>`;

export const dataAttrs = attrs =>
  Object.entries(attrs)
    .map(([key, value]) => ` data-${h(key)}="${h(value)}"`)
    .join('');

export const empty = (title, message = '') =>
  `<div class="empty"><span class="empty-icon" aria-hidden="true">◎</span><h3>${h(title)}</h3>${message ? `<p>${h(message)}</p>` : ''}</div>`;

export const section = (title, body, aside = '', extraClass = '') =>
  `<section class="panel ${h(extraClass)}"><div class="section-head"><h2>${h(title)}</h2>${aside}</div>${body}</section>`;

export const metric = (title, value, note = '') =>
  `<article class="metric"><span>${h(title)}</span><strong>${h(value)}</strong>${note ? `<small>${h(note)}</small>` : ''}</article>`;

export const input = (name, title, { type = 'text', value = '', required = false, hint = '', attrs = '' } = {}) =>
  `<label>${h(title)}<input name="${h(name)}" type="${h(type)}" value="${h(value)}"${required ? ' required' : ''}${type === 'number' ? ' min="0" step="any"' : ''} ${attrs}>${hint ? `<small>${h(hint)}</small>` : ''}</label>`;

export const area = (name, title, value = '') =>
  `<label class="wide">${h(title)}<textarea name="${h(name)}" rows="3">${h(value)}</textarea></label>`;

export const select = (name, title, options, value = '') =>
  `<label>${h(title)}<select name="${h(name)}">${options
    .map(option => `<option value="${h(option)}"${option === value ? ' selected' : ''}>${h(enumLabel(option))}</option>`)
    .join('')}</select></label>`;

export const check = (name, title, checked = false, extraClass = '') =>
  `<label class="check ${h(extraClass)}"><input name="${h(name)}" type="checkbox"${checked ? ' checked' : ''}> ${h(title)}</label>`;

export const form = (action, fields, submit, attrs = {}, { disabled = false } = {}) =>
  `<form data-action="${h(action)}"${dataAttrs(attrs)} novalidate><div class="form-grid">${fields}</div><p class="form-error" role="alert"></p><div class="actions"><button class="primary" type="submit"${disabled ? ' disabled' : ''}>${h(submit)}</button></div></form>`;

export const table = (headers, rows, emptyTitle = 'Nothing here yet') =>
  rows.length
    ? `<div class="table-wrap"><table><thead><tr>${headers.map(t => `<th scope="col">${h(t)}</th>`).join('')}</tr></thead><tbody>${rows
        .map(row => `<tr>${row.map(cell => `<td>${cell}</td>`).join('')}</tr>`)
        .join('')}</tbody></table></div>`
    : empty(emptyTitle);

export const list = (items, emptyText = '') =>
  items.length ? `<ul class="bullets">${items.map(item => `<li>${item}</li>`).join('')}</ul>` : emptyText ? `<p>${h(emptyText)}</p>` : '';

export const note = (text, tone = 'warn') => `<p class="note ${h(tone)}">${h(text)}</p>`;

export const meter = (value, labelText) =>
  `<meter min="0" max="100" low="40" high="70" optimum="100" value="${h(value)}" aria-label="${h(labelText)}"></meter>`;
