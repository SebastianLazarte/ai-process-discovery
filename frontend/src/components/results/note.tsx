import type { ReactNode } from "react";

// The note of the vanilla client (.note in web/styles.css): a bordered aside in warn or info.
const TONES = {
  warn: "border-warn bg-warn-bg text-warn-ink",
  info: "border-info bg-info-bg text-ink-soft",
} as const;

export function Note({
  tone = "warn",
  children,
}: {
  tone?: keyof typeof TONES;
  children: ReactNode;
}) {
  return (
    <p className={`mb-4 rounded-r-control border-l-[3px] px-4 py-3 text-[13px] ${TONES[tone]}`}>
      {children}
    </p>
  );
}
