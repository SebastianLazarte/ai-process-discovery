import { shortId } from "@/lib/format";

import { Panel } from "./panel";

// The Blueprint tab. Stub until RS-94 builds it; that work owns this file.
export function BlueprintView({ analysisId }: { id: string; analysisId: string }) {
  return (
    <Panel id="blueprint-title" title="Blueprint">
      <p className="text-[13px] text-muted">
        The blueprint of analysis {shortId(analysisId)} arrives with the next release of this
        client.
      </p>
    </Panel>
  );
}
