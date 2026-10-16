"use client";

import { useMeta } from "@/lib/api/queries";

// RS-73: on the public demo every page warns that data is shared and short-lived (RS-62).
export function DemoBanner() {
  const meta = useMeta();
  if (!meta.data?.public_demo) return null;
  return (
    <p
      role="note"
      className="border-b border-line bg-warn-bg px-4 py-2.5 text-[13px] text-warn-ink md:px-11"
    >
      <strong>Public demo {`v${meta.data.version}`}.</strong> Anything you enter is visible to other
      visitors and deleted daily. Do not enter real or personal data.
    </p>
  );
}
