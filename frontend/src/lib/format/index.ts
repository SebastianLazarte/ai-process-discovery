// The only module that turns API values into text (hard rule 7, ADR 0009). It prints the
// figures the API returns and never computes one: Intl only rounds for display. The rules
// match web/format.js, so both clients show the same text during the migration.

export const UNKNOWN = "unknown";

const fixed = (value: number | string, digits: number) =>
  Number(value).toLocaleString("en-US", {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  });

/** A money amount as the API sends it (a decimal string), or unknown. Never 0 for null. */
export function money(value: string | number | null | undefined): string {
  return value === null || value === undefined ? UNKNOWN : fixed(value, 2);
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
