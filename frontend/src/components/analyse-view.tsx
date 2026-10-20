import Link from "next/link";

import { Panel } from "./panel";

// The Analyse tab. Stub until RS-75 builds it; that work owns this file.
export function AnalyseView({ id }: { id: string }) {
  return (
    <Panel id="analyse-title" title="Analyse">
      <p className="text-[13px] text-muted">
        Running an analysis arrives with the next release of this client. Until then, review the{" "}
        <Link href={`/processes/${id}`}>steps</Link>.
      </p>
    </Panel>
  );
}
