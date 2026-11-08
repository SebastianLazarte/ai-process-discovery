import type { ReactNode } from "react";

// A provenance chip (ADR 0018): rules version, LLM status, prompt version or process
// version, small and monospaced, on the ground colour so it reads on any surface. Always
// on screen, never hidden behind a toggle.
export function Chip({ children }: { children: ReactNode }) {
  return (
    <span className="inline-flex items-center rounded-chip bg-bg px-2 py-1 font-mono text-xs leading-none whitespace-nowrap text-muted">
      {children}
    </span>
  );
}

/** A row of chips that wraps on a narrow screen. */
export function Chips({ label, children }: { label: string; children: ReactNode }) {
  return (
    <ul aria-label={label} className="flex flex-wrap gap-2">
      {children}
    </ul>
  );
}

/** One chip in a Chips row. */
export function ChipItem({ children }: { children: ReactNode }) {
  return (
    <li>
      <Chip>{children}</Chip>
    </li>
  );
}
