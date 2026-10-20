import Link from "next/link";

import { Panel } from "./panel";

// The History tab. Stub until RS-93 builds it; that work owns this file.
export function HistoryView({ id }: { id: string }) {
  return (
    <Panel id="history-title" title="History">
      <p className="text-[13px] text-muted">
        The analysis history arrives with the next release of this client. Until then, review the{" "}
        <Link href={`/processes/${id}`}>steps</Link>.
      </p>
    </Panel>
  );
}
