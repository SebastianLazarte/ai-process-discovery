import type { ReactNode } from "react";

import type { AnalysisRead } from "@/lib/api/queries";
import { enumLabel, hours, money, months, percent, score, shortId } from "@/lib/format";

import { Badge } from "../badge";
import { Meter } from "../meter";
import { Panel } from "../panel";
import { Note } from "./note";
import {
  NO_HOURLY_COST,
  NO_IMPLEMENTATION_COST,
  NO_TIME,
  paybackReason,
  roiReason,
  unknownNote,
} from "./reasons";
import { SourceBadge } from "./source-badge";

// The four panels of Results, as in web/analysis-views.js. Suitability, business impact,
// risk and human controls stay apart, and nothing combines them into one score (RS-53).

/** Two panels across on a wide screen, one below 1150 px, as .quads in web/styles.css. */
export function Quads({ children }: { children: ReactNode }) {
  return <div className="grid gap-6 min-[1151px]:grid-cols-2">{children}</div>;
}

/** The bulleted list of the vanilla client (.bullets), or a sentence when it is empty. */
function Bullets({ items, empty }: { items: ReactNode[]; empty?: string }) {
  if (items.length === 0) return empty ? <p className="mb-4 text-sm">{empty}</p> : null;
  return (
    <ul className="mb-3.5">
      {items.map((item, index) => (
        <li
          key={index}
          className="border-t border-line py-[9px] text-sm text-ink-soft first:border-t-0"
        >
          {item}
        </li>
      ))}
    </ul>
  );
}

export function SuitabilityPanel({ analysis }: { analysis: AnalysisRead }) {
  const suitability = analysis.automation_suitability;
  const reason = unknownNote(suitability.process_score, NO_TIME);
  return (
    <Panel
      id="suitability-title"
      title="Automation suitability"
      action={<small className="text-xs text-muted">{suitability.policy_version}</small>}
    >
      <p className="mb-3 text-[52px] leading-none font-semibold tracking-[-2px] text-ink">
        {score(suitability.process_score)}
        {!reason && <small className="text-lg tracking-normal"> / 100</small>}
      </p>
      {reason && <p className="mb-3 text-[13px] text-muted">{reason}</p>}
      <p className="mb-4 text-[15px] text-muted">
        Whether a step can be automated, weighted by the time it takes. It says nothing about
        whether it is worth it.
      </p>
      <ul aria-label="Suitability by step">
        {analysis.step_assessments.map((step) => (
          <li
            key={step.step_id}
            className="grid grid-cols-[minmax(0,1fr)_80px_28px] items-center gap-3 border-t border-line py-[7px] text-[13px] md:grid-cols-[minmax(0,1fr)_120px_32px]"
          >
            <span className="truncate">
              {step.position}. {step.name}
            </span>
            <Meter value={step.suitability_score} label={`${step.name} suitability`} />
            <b className="text-right tabular-nums">{score(step.suitability_score)}</b>
          </li>
        ))}
      </ul>
    </Panel>
  );
}

function MiniMetric({ term, value, note }: { term: string; value: string; note?: string }) {
  return (
    <div className="min-w-0 rounded-panel border border-line bg-surface-raised px-3.5 py-3">
      <dt className="text-xs text-muted">{term}</dt>
      <dd className="text-[19px] leading-snug font-semibold tracking-[-0.5px] break-words tabular-nums">
        {value}
      </dd>
      {note && <dd className="text-xs text-muted">{note}</dd>}
    </div>
  );
}

export function ImpactPanel({
  analysis,
  stepNames,
}: {
  analysis: AnalysisRead;
  stepNames: Readonly<Record<string, string>>;
}) {
  const impact = analysis.business_impact;
  const missing = impact.steps_without_reduction.map((id) => stepNames[id] ?? shortId(id));
  return (
    <Panel id="impact-title" title="Business impact">
      <dl className="mb-4 grid grid-cols-2 gap-2.5 min-[1151px]:grid-cols-3">
        <MiniMetric term="Hours freed / month" value={hours(impact.estimated_hours_saved)} />
        <MiniMetric
          term="Net savings / month"
          value={money(impact.net_monthly_savings)}
          note={unknownNote(impact.net_monthly_savings, NO_HOURLY_COST)}
        />
        <MiniMetric
          term="Payback"
          value={months(impact.payback_months)}
          note={unknownNote(impact.payback_months, paybackReason(impact))}
        />
        <MiniMetric
          term="Gross savings / month"
          value={money(impact.estimated_monthly_savings)}
          note={unknownNote(impact.estimated_monthly_savings, NO_HOURLY_COST)}
        />
        <MiniMetric
          term="Implementation cost"
          value={money(impact.implementation_cost)}
          note={
            unknownNote(impact.implementation_cost, NO_IMPLEMENTATION_COST) ?? "Your assumption"
          }
        />
        <MiniMetric
          term="ROI at 12 months"
          value={percent(impact.roi_12_months)}
          note={unknownNote(impact.roi_12_months, roiReason(impact))}
        />
      </dl>
      {missing.length > 0 && (
        <Note tone="info">
          No expected reduction given for {missing.join(", ")}. They count as zero.
        </Note>
      )}
      <p className="text-[15px] text-muted">
        Computed from your assumptions only. An unknown hourly cost leaves savings, payback and ROI
        unknown.
      </p>
    </Panel>
  );
}

export function RiskPanel({ analysis }: { analysis: AnalysisRead }) {
  const risks = analysis.risks.map((risk) => (
    <>
      <SourceBadge source={risk.source} /> <b>{enumLabel(risk.type)}</b>: {risk.description}
    </>
  ));
  return (
    <Panel id="risk-title" title="Risk">
      <Bullets items={risks} empty="No risks flagged." />
      {analysis.unknowns.length > 0 && (
        <>
          <h3 className="mb-1.5 text-[15px] font-semibold">Unknowns</h3>
          <Bullets items={analysis.unknowns} />
        </>
      )}
    </Panel>
  );
}

export function ControlsPanel({ analysis }: { analysis: AnalysisRead }) {
  const controls = analysis.human_controls.map((control) => (
    <>
      <Badge value={control.control} /> <b>{control.step_name}</b>: {control.reasons.join("; ")}
    </>
  ));
  return (
    <Panel id="controls-title" title="Human controls">
      <Bullets items={controls} empty="No human control required by the rules." />
      <p className="text-[15px] text-muted">The LLM can raise a control and never lower one.</p>
    </Panel>
  );
}
