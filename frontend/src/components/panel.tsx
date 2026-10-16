import type { ReactNode } from "react";

// The panel of the vanilla client: a titled surface with an optional action at the right.
export function Panel({
  id,
  title,
  action,
  children,
  className = "",
}: {
  id: string;
  title: string;
  action?: ReactNode;
  children: ReactNode;
  className?: string;
}) {
  return (
    <section
      aria-labelledby={id}
      className={`min-w-0 rounded-panel border border-line bg-surface p-6 ${className}`}
    >
      <div className="mb-[18px] flex flex-wrap items-center justify-between gap-3">
        <h2 id={id} className="text-[17px] leading-snug font-semibold tracking-tight">
          {title}
        </h2>
        {action}
      </div>
      {children}
    </section>
  );
}

/** The small uppercase label above a page title. */
export function Eyebrow({ children }: { children: ReactNode }) {
  return (
    <p className="mb-3 text-[10px] font-semibold tracking-[2.3px] text-accent uppercase">
      {children}
    </p>
  );
}
