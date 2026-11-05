import type { AnalysisRead } from "@/lib/api/queries";
import { hours, money, months, percent, shortId, timestamp, version } from "@/lib/format";

import { ChipItem, Chips } from "../chip";
import { NO_HOURLY_COST, paybackReason, roiReason, unknownNote } from "./reasons";

// The answer first (RS-107, ADR 0018): Results opens on how much the process saves a month
// and when it pays back, as the API returns them, with the provenance of those figures in
// chips beside them. A figure the API left null reads unknown with its reason, never 0.
// The band only repeats figures of the Business impact panel; it never merges suitability,
// impact, risk and controls into one score.

type Llm = AnalysisRead["llm"];

export function llmLabel(llm: Llm): string {
  if (llm.status === "not_requested") return "LLM not requested";
  return `LLM ${llm.status}${llm.model ? ` · ${llm.provider}/${llm.model}` : ""}`;
}

export function AnswerBand({ analysis }: { analysis: AnalysisRead }) {
  const impact = analysis.business_impact;
  const netReason = unknownNote(impact.net_monthly_savings, NO_HOURLY_COST);

  return (
    <section aria-labelledby="answer-title" className="mb-6 rounded-band bg-band p-6 md:p-7">
      <h2 id="answer-title" className="sr-only">
        The answer
      </h2>
      <dl className="grid gap-6">
        <div className="min-w-0">
          <dt className="text-sm text-muted">Net savings / month</dt>
          <dd className="text-[40px] leading-tight font-semibold tracking-[-1.5px] break-words text-accent tabular-nums md:text-figure">
            {money(impact.net_monthly_savings)}
          </dd>
          {netReason && <dd className="text-sm text-ink-soft">{netReason}</dd>}
        </div>
        <div className="grid gap-4 sm:grid-cols-3">
          <Figure
            term="Payback"
            value={months(impact.payback_months)}
            note={unknownNote(impact.payback_months, paybackReason(impact))}
          />
          <Figure term="Hours freed / month" value={hours(impact.estimated_hours_saved)} />
          <Figure
            term="ROI at 12 months"
            value={percent(impact.roi_12_months)}
            note={unknownNote(impact.roi_12_months, roiReason(impact))}
          />
        </div>
      </dl>
      <div className="mt-6">
        <Chips label="Provenance">
          <ChipItem>rules {analysis.rules_version}</ChipItem>
          <ChipItem>{llmLabel(analysis.llm)}</ChipItem>
          <ChipItem>prompt {analysis.llm.prompt_version ?? "none"}</ChipItem>
          <ChipItem>process {version(analysis.process_version)}</ChipItem>
          <ChipItem>analysis {shortId(analysis.id)}</ChipItem>
          <ChipItem>{timestamp(analysis.created_at)}</ChipItem>
        </Chips>
      </div>
    </section>
  );
}

function Figure({ term, value, note }: { term: string; value: string; note?: string }) {
  return (
    <div className="min-w-0">
      <dt className="text-xs text-muted">{term}</dt>
      <dd className="text-xl leading-snug font-semibold break-words tabular-nums">{value}</dd>
      {note && <dd className="text-xs text-ink-soft">{note}</dd>}
    </div>
  );
}
