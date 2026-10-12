// Presentation of figures the API has already computed (ADR 0007, RS-50).
// This is the only module allowed to turn API strings into numbers, and only to print
// them. Nothing here adds, multiplies or rounds a metric on its own: Intl does the
// display rounding and the percent scaling.

const UNKNOWN = 'unknown';
const NOT_APPLICABLE = 'n/a';

const fixed = (value, digits) =>
  Number(value).toLocaleString('en-US', { minimumFractionDigits: digits, maximumFractionDigits: digits });

export const money = value => (value === null || value === undefined ? UNKNOWN : fixed(value, 2));

export const number = (value, digits = 2) =>
  value === null || value === undefined ? NOT_APPLICABLE : fixed(value, digits);

export const hours = value => (value === null || value === undefined ? UNKNOWN : `${fixed(value, 2)} h`);

export const months = value =>
  value === null || value === undefined ? NOT_APPLICABLE : `${fixed(value, 1)} mo`;

export const percent = (ratio, digits = 0) =>
  ratio === null || ratio === undefined || ratio === ''
    ? NOT_APPLICABLE
    : Number(ratio).toLocaleString('en-US', {
        style: 'percent',
        minimumFractionDigits: digits,
        maximumFractionDigits: digits,
      });

export const score = value => (value === null || value === undefined ? NOT_APPLICABLE : fixed(value, 0));

export const timestamp = iso => (iso ? `${iso.slice(0, 10)} ${iso.slice(11, 16)} UTC` : '');

const ACRONYMS = { ai: 'AI', api: 'API', llm: 'LLM', erp: 'ERP', crm: 'CRM' };

export const enumLabel = value => {
  if (!value) return '';
  const words = String(value).toLowerCase().split('_').map(word => ACRONYMS[word] ?? word);
  return words.join(' ').replace(/^./, c => c.toUpperCase());
};

// Server-written details sometimes carry a raw enum (DIGITAL_STRUCTURED); prose passes through.
export const detail = value => (/^[A-Z][A-Z_]*$/.test(String(value)) ? enumLabel(value) : String(value ?? ''));

export const shortId = id => String(id ?? '').slice(0, 8);
