import type { ReactNode } from "react";

import { InfoIcon, WarningIcon } from "./icons";

// A note on Graphite (ADR 0018): a tinted card with its icon, raised by its colour and with
// no border, in place of the left-bordered aside of the vanilla client.
const TONES = {
  info: "bg-info-bg text-ink-soft",
  warn: "bg-warn-bg text-warn-ink",
  bad: "bg-bad-bg text-ink",
} as const;

const ICON_TONES = { info: "text-info", warn: "text-warn", bad: "text-bad" } as const;

export type NoteTone = keyof typeof TONES;

/** The surface of a note, for a container that is not a Note itself. */
export function noteClass(tone: NoteTone): string {
  return `rounded-card px-4 py-3 text-[13px] ${TONES[tone]}`;
}

export function Note({
  tone = "warn",
  role,
  className = "mb-4",
  children,
}: {
  tone?: NoteTone;
  role?: "note" | "alert";
  className?: string;
  children: ReactNode;
}) {
  const Icon = tone === "info" ? InfoIcon : WarningIcon;
  return (
    <div role={role} className={`flex gap-3 ${noteClass(tone)} ${className}`}>
      <Icon className={`mt-px size-4 ${ICON_TONES[tone]}`} />
      <div className="min-w-0 flex-1">{children}</div>
    </div>
  );
}
