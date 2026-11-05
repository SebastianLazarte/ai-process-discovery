import type { ReactNode } from "react";

import { enumLabel } from "@/lib/format";

// The badge of the vanilla client, on Graphite (ADR 0018). Its tone follows the value, as
// toneOf in web/views.js: the colour means the same thing on every screen. The language of
// trust of the design brief adds two: an AI suggestion is dashed in the reserved AI tone,
// and a required human control is filled.

export type Tone = "good" | "info" | "warn" | "bad" | "ai" | "required" | "neutral";

const TONES: Readonly<Record<Exclude<Tone, "neutral">, readonly string[]>> = {
  good: ["RULE_BASED", "API_INTEGRATION", "NONE", "ok"],
  info: ["AI_CANDIDATE", "HYBRID", "RULES"],
  warn: ["RECOMMENDED", "NEEDS_REVIEW", "unavailable", "HUMAN"],
  bad: ["MANUAL"],
  ai: ["AI"],
  required: ["REQUIRED"],
};

export function toneOf(value: string | null | undefined): Tone {
  for (const tone of ["good", "info", "warn", "bad", "ai", "required"] as const) {
    if (value && TONES[tone].includes(value)) return tone;
  }
  return "neutral";
}

const CLASSES: Readonly<Record<Tone, string>> = {
  good: "border-transparent bg-good-bg text-good",
  info: "border-transparent bg-info-bg text-info",
  warn: "border-transparent bg-warn-bg text-warn",
  bad: "border-transparent bg-bad-bg text-bad",
  ai: "border-dashed border-ai bg-transparent text-ai",
  required: "border-transparent bg-required text-required-ink",
  neutral: "border-transparent bg-surface-raised text-ink-soft",
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
      className={`inline-block rounded-chip border px-2 py-[3px] align-middle text-[11px] leading-[1.4] font-semibold whitespace-nowrap ${CLASSES[tone]}`}
    >
      {children ?? enumLabel(value)}
    </span>
  );
}
