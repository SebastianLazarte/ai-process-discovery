"use client";

import { useMeta } from "@/lib/api/queries";

// RS-73: on the public demo every page warns that data is shared and short-lived (RS-62).
// Graphite (RS-109, ADR 0018): one slim line with a status dot, the full text kept.
export function DemoBanner() {
  const meta = useMeta();
  if (!meta.data?.public_demo) return null;
  return (
    <p
      role="note"
      className="flex items-start gap-2.5 bg-sidebar px-4 py-2 text-[13px] leading-5 text-ink-soft md:items-center md:px-11"
    >
      <span aria-hidden="true" className="mt-1.5 size-2 shrink-0 rounded-full bg-warn md:mt-0" />
      <span>
        <strong className="font-semibold text-ink">Public demo {`v${meta.data.version}`}.</strong>{" "}
        Anything you enter is visible to other visitors and deleted daily. Do not enter real or
        personal data.
      </span>
    </p>
  );
}
