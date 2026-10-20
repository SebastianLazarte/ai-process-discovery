import type { ReactNode } from "react";

import { enumLabel } from "@/lib/format";

// The badge of the vanilla client. Its tone follows the value, as toneOf in web/views.js:
// the colour means the same thing on every screen.

export type Tone = "good" | "info" | "warn" | "bad" | "neutral";

const TONES: Readonly<Record<Exclude<Tone, "neutral">, readonly string[]>> = {
  good: ["RULE_BASED", "API_INTEGRATION", "NONE", "ok"],
  info: ["AI_CANDIDATE", "HYBRID", "AI", "RULES"],
  warn: ["RECOMMENDED", "NEEDS_REVIEW", "unavailable", "HUMAN"],
  bad: ["REQUIRED", "MANUAL"],
};

export function toneOf(value: string | null | undefined): Tone {
  for (const tone of ["good", "info", "warn", "bad"] as const) {
    if (value && TONES[tone].includes(value)) return tone;
  }
  return "neutral";
}

const CLASSES: Readonly<Record<Tone, string>> = {
  good: "border-good/40 bg-good-bg text-good",
  info: "border-info/40 bg-info-bg text-info",
  warn: "border-warn/40 bg-warn-bg text-warn",
  bad: "border-bad/40 bg-bad-bg text-bad",
  neutral: "border-line bg-surface-raised text-ink-soft",
};

/** A value as a badge: its label from enumLabel unless children say otherwise. */
export function Badge({
  value,
  tone = toneOf(value),
  children,
}: {
  value?: string | null;
  tone?: Tone;
  children?: ReactNode;
}) {
  return (
    <span
      data-tone={tone}
      className={`inline-block rounded-[5px] border px-2 py-[3px] align-middle text-[11px] leading-[1.4] whitespace-nowrap ${CLASSES[tone]}`}
    >
      {children ?? enumLabel(value)}
    </span>
  );
}
