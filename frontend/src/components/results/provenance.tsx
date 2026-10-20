import type { AnalysisRead } from "@/lib/api/queries";
import { shortId, timestamp, version } from "@/lib/format";

import { Badge } from "../badge";

// Where the figures come from (RS-92): the analysis, its process version, the rules version,
// the LLM status and the prompt version, as provenance() in web/analysis-views.js. The note
// for an unavailable LLM belongs to RS-75, which adds it below this bar.

type Llm = AnalysisRead["llm"];

function llmLabel(llm: Llm): string {
  if (llm.status === "not_requested") return "LLM not requested";
  return `LLM ${llm.status}${llm.model ? ` · ${llm.provider}/${llm.model}` : ""}`;
}

export function ProvenanceBar({ analysis }: { analysis: AnalysisRead }) {
  const llm = analysis.llm;
  return (
    <section aria-label="Provenance" className="mb-[18px] text-[13px] text-muted">
      <p>
        Analysis <code className="text-xs break-all">{shortId(analysis.id)}</code> ·{" "}
        {timestamp(analysis.created_at)} · process {version(analysis.process_version)} · rules{" "}
        {analysis.rules_version} · <Badge value={llm.status}>{llmLabel(llm)}</Badge> · prompt{" "}
        {llm.prompt_version ?? "none"}
      </p>
    </section>
  );
}
