import type { ReactNode } from "react";

// The metric cards of the vanilla client: a term, its figure as text from lib/format, and
// an optional note. Metrics lays them out four across, as .metrics in web/styles.css.

export function Metrics({ children, className = "" }: { children: ReactNode; className?: string }) {
  return (
    <dl className={`mb-6 grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4 ${className}`}>
      {children}
    </dl>
  );
}

export function Metric({ term, value, note }: { term: string; value: string; note?: string }) {
  return (
    <div className="min-w-0 rounded-panel border border-line bg-surface px-5 py-[18px]">
      <dt className="text-xs text-muted">{term}</dt>
      <dd className="text-[26px] leading-snug font-semibold tracking-[-0.5px] break-words tabular-nums">
        {value}
      </dd>
      {note && <dd className="text-xs text-muted">{note}</dd>}
    </div>
  );
}
