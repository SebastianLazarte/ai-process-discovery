import { shortId } from "@/lib/format";

import { Panel } from "./panel";

// The Results tab. Stub until RS-92 builds it; that work owns this file.
export function ResultsView({ analysisId }: { id: string; analysisId: string }) {
  return (
    <Panel id="results-title" title="Results">
      <p className="text-[13px] text-muted">
        The results of analysis {shortId(analysisId)} arrive with the next release of this client.
      </p>
    </Panel>
  );
}
