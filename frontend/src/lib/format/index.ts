// The only module that turns API values into text (hard rule 7, ADR 0009). It prints the
// figures the API returns and never computes one: Intl only rounds for display and scales a
// ratio to a percent. The rules match web/format.js, so both clients show the same text
// during the migration, with one change: a missing figure always reads UNKNOWN, never n/a.

export const UNKNOWN = "unknown";

/** A figure as the API sends it: decimals travel as strings, counts as numbers. */
type Figure = string | number | null | undefined;

const missing = (value: Figure): value is null | undefined | "" =>
  value === null || value === undefined || value === "";

const fixed = (value: number | string, digits: number) =>
  Number(value).toLocaleString("en-US", {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  });

/** A money amount as the API sends it (a decimal string), or unknown. Never 0 for null. */
export function money(value: Figure): string {
  return missing(value) ? UNKNOWN : fixed(value, 2);
}

export function number(value: Figure, digits = 2): string {
  return missing(value) ? UNKNOWN : fixed(value, digits);
}

export function hours(value: Figure): string {
  return missing(value) ? UNKNOWN : `${fixed(value, 2)} h`;
}

export function months(value: Figure): string {
  return missing(value) ? UNKNOWN : `${fixed(value, 1)} mo`;
}

/** A ratio (0.25) as a percent (25%). */
export function percent(ratio: Figure, digits = 0): string {
  return missing(ratio)
    ? UNKNOWN
    : Number(ratio).toLocaleString("en-US", {
        style: "percent",
        minimumFractionDigits: digits,
        maximumFractionDigits: digits,
      });
}

export function score(value: Figure): string {
  return missing(value) ? UNKNOWN : fixed(value, 0);
}

export function count(value: number): string {
  return fixed(value, 0);
}

export function steps(value: number): string {
  return value === 1 ? "1 step" : `${count(value)} steps`;
}

export function version(value: number): string {
  return `v${value}`;
}

export function timestamp(iso: string): string {
  return `${iso.slice(0, 10)} ${iso.slice(11, 16)} UTC`;
}

const ACRONYMS: Readonly<Record<string, string>> = {
  ai: "AI",
  api: "API",
  llm: "LLM",
  erp: "ERP",
  crm: "CRM",
};

/** An enum value as words: AI_CANDIDATE reads "AI candidate". */
export function enumLabel(value: string | null | undefined): string {
  if (!value) return "";
  const words = value
    .toLowerCase()
    .split("_")
    .map((word) => ACRONYMS[word] ?? word);
  return words.join(" ").replace(/^./, (first) => first.toUpperCase());
}

/** Server-written details sometimes carry a raw enum (DIGITAL_STRUCTURED); prose passes through. */
export function detail(value: string | number | null | undefined): string {
  const text = String(value ?? "");
  return /^[A-Z][A-Z_]*$/.test(text) ? enumLabel(text) : text;
}

/** The first block of a UUID, enough to tell analyses apart in a table. */
export function shortId(id: string | null | undefined): string {
  return (id ?? "").slice(0, 8);
}
