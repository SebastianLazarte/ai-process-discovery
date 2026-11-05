import type { ReactNode } from "react";

import { InfoIcon } from "./icons";

// Empty states and skeletons on Graphite (RS-109, ADR 0018). An empty state says what is
// missing and offers a way on, never a bare heading. A skeleton takes the shape and size of
// the content it stands for, so nothing jumps when the data arrives; screen readers hear
// one status line instead of the grey shapes.

export function EmptyState({
  title,
  children,
  action,
  icon,
  compact = false,
}: {
  title: string;
  children?: ReactNode;
  /** The way on: a link or a button. */
  action?: ReactNode;
  icon?: ReactNode;
  compact?: boolean;
}) {
  if (compact) {
    return (
      <div className="mx-2.5 rounded-card bg-surface p-3">
        <h3 className="text-sm font-semibold">{title}</h3>
        {children && <p className="mt-1 text-xs text-muted">{children}</p>}
        {action && <div className="mt-2 flex flex-col gap-1 text-sm">{action}</div>}
      </div>
    );
  }
  return (
    <div className="px-3 py-8 text-center">
      <span
        aria-hidden="true"
        className="mx-auto mb-3 flex size-11 items-center justify-center rounded-full bg-surface-raised text-muted"
      >
        {icon ?? <InfoIcon />}
      </span>
      <h3 className="mb-1 text-[15px] font-semibold">{title}</h3>
      {children && <p className="mx-auto max-w-[360px] text-[13px] text-muted">{children}</p>}
      {action && <div className="mt-4 flex flex-wrap justify-center gap-2">{action}</div>}
    </div>
  );
}

/** One grey shape of a skeleton, on the raised surface unless it stands for a panel. */
export function Bone({ className }: { className: string }) {
  return <div className={`animate-pulse motion-reduce:animate-none ${className}`} />;
}

/** A skeleton: one status line for screen readers, and the shapes hidden from them. */
export function Skeleton({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div role="status" aria-label={label} aria-busy="true">
      <span className="sr-only">{label}…</span>
      <div aria-hidden="true">{children}</div>
    </div>
  );
}

/** The title and tabs of a process page, then a panel. */
export function ProcessSkeleton() {
  return (
    <Skeleton label="Loading the process">
      <div className="mb-6">
        <Bone className="mb-3 h-3 w-28 rounded-chip bg-surface-raised" />
        <Bone className="mb-3 h-[31px] w-2/3 max-w-xl rounded-control bg-surface-raised md:h-[38px]" />
        <Bone className="h-4 w-full max-w-[760px] rounded-chip bg-surface-raised" />
      </div>
      <Bone className="mb-7 h-[52px] w-[430px] max-w-full rounded-panel bg-surface" />
      <Bone className="h-72 rounded-panel bg-surface" />
    </Skeleton>
  );
}

/** The answer band, the current state and the four panels of Results. */
export function ResultsSkeleton() {
  return (
    <Skeleton label="Loading the analysis">
      <Bone className="mb-6 h-[268px] rounded-band bg-band md:h-[292px]" />
      <div className="mb-6 grid grid-cols-1 gap-4 sm:grid-cols-2">
        <Bone className="h-[92px] rounded-panel bg-surface" />
        <Bone className="h-[92px] rounded-panel bg-surface" />
      </div>
      <div className="grid gap-6 min-[1151px]:grid-cols-2">
        {[0, 1, 2, 3].map((panel) => (
          <Bone key={panel} className="h-80 rounded-panel bg-surface" />
        ))}
      </div>
    </Skeleton>
  );
}

/** The download row and the first sections of the Blueprint. */
export function BlueprintSkeleton() {
  return (
    <Skeleton label="Loading the blueprint">
      <div className="mb-5 flex flex-wrap items-center justify-between gap-4">
        <Bone className="h-4 w-80 max-w-full rounded-chip bg-surface-raised" />
        <Bone className="h-11 w-40 rounded-control bg-surface-raised" />
      </div>
      <div className="grid gap-6">
        {[0, 1, 2].map((section) => (
          <Bone key={section} className="h-56 rounded-panel bg-surface" />
        ))}
      </div>
    </Skeleton>
  );
}

/** Three demo cards, in the grid of the real ones. */
export function DemoCardsSkeleton() {
  return (
    <Skeleton label="Loading demos">
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {[0, 1, 2].map((card) => (
          <Bone key={card} className="h-[212px] rounded-card bg-surface-raised" />
        ))}
      </div>
    </Skeleton>
  );
}

/** The process links of the sidebar: a row on a narrow screen where the list folds. */
export function ProcessListSkeleton({ fold }: { fold: boolean }) {
  return (
    <Skeleton label="Loading processes">
      <div className={fold ? "flex gap-1.5 md:block md:space-y-1.5" : "space-y-1.5"}>
        {[0, 1, 2].map((row) => (
          <Bone
            key={row}
            className={`h-[50px] rounded-control bg-surface ${fold ? "w-40 flex-none md:w-auto" : ""}`}
          />
        ))}
      </div>
    </Skeleton>
  );
}
