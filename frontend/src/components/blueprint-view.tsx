"use client";

import type { ReactNode } from "react";

import { blueprintMarkdownUrl, useBlueprint, useProcess } from "@/lib/api/queries";
import type { components } from "@/lib/api/schema";
import {
  enumLabel,
  hours,
  money,
  months,
  number,
  percent,
  score,
  shortId,
  timestamp,
} from "@/lib/format";

import { Badge } from "./badge";
import { buttonClass } from "./button";
import { DataTable } from "./data-table";
import type { Column } from "./data-table";
import { Metric } from "./metric";
import { Panel } from "./panel";

type Blueprint = components["schemas"]["Blueprint"];
type Opportunity = components["schemas"]["BlueprintStep"];

// The Blueprint tab (RS-94), as blueprintPage in web/analysis-views.js: the eight sections
// of GET /analyses/{id}/blueprint, every value printed as text. The Markdown download is a
// plain link to the API's own file, so the browser saves its bytes and no client code reads
// or rebuilds them.
export function BlueprintView({ id, analysisId }: { id: string; analysisId: string }) {
  const blueprint = useBlueprint(analysisId);
  const process = useProcess(id);

  if (blueprint.isPending)
    return <p className="py-24 text-center text-muted">Loading the blueprint…</p>;
  if (blueprint.isError)
    return <p className="py-24 text-center text-muted">The blueprint could not be loaded.</p>;

  const stepNames = new Map((process.data?.steps ?? []).map((step) => [step.id, step.name]));
  const data = blueprint.data;
  return (
    <>
      <div className="mb-5 flex flex-wrap items-center justify-between gap-4">
        <p className="text-muted">
          Eight sections, built from the analysis with every override applied.
        </p>
        <a
          href={blueprintMarkdownUrl(data.analysis_id)}
          download={`blueprint-${shortId(data.analysis_id)}.md`}
          className={buttonClass("primary")}
        >
          Download .md
        </a>
      </div>
      <ProcessSummary summary={data.process_summary} />
      <Section n={2} title="Current state">
        <dl className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <Metric term="Monthly hours" value={hours(data.current_state.monthly_hours)} />
          <Metric term="Monthly cost" value={money(data.current_state.monthly_cost)} />
        </dl>
      </Section>
      <Section
        n={3}
        title="Automation opportunities"
        aside={<small className="text-xs text-muted">Ordered by monthly hours</small>}
      >
        {data.automation_opportunities.length ? (
          <DataTable
            labelledBy="blueprint-3"
            columns={OPPORTUNITY_COLUMNS}
            rows={data.automation_opportunities}
            rowKey={(row) => `${row.position}`}
          />
        ) : (
          <Empty title="Nothing here yet" />
        )}
      </Section>
      <Section n={4} title="Proposed architecture">
        <Bullets items={data.proposed_architecture} empty="No architecture proposed." />
      </Section>
      <BusinessImpact impact={data.business_impact} stepNames={stepNames} />
      <Section n={6} title="Risks">
        <Bullets
          items={data.risks.map((risk) => (
            <>
              <Badge value={risk.source} /> {risk.description}
            </>
          ))}
          empty="No risks flagged."
        />
      </Section>
      <Section n={7} title="Human controls">
        <Bullets
          items={data.human_controls.map((control) => (
            <>
              <Badge value={control.control} /> <strong>{control.step_name}</strong>:{" "}
              {control.reasons.join("; ")}
            </>
          ))}
          empty="No human control required."
        />
      </Section>
      <Section n={8} title="Workflow specification">
        {data.workflow_specification.length ? (
          <ol className="m-0 list-decimal pl-[22px]">
            {data.workflow_specification.map((line, index) => (
              <li key={index} className="py-1.5 text-sm text-ink-soft">
                {line}
              </li>
            ))}
          </ol>
        ) : (
          <Empty title="No workflow" />
        )}
      </Section>
    </>
  );
}

const OPPORTUNITY_COLUMNS: readonly Column<Opportunity>[] = [
  { header: "#", cell: (row) => row.position },
  { header: "Step", cell: (row) => <strong>{row.name}</strong> },
  { header: "Method", cell: (row) => <Badge value={row.method} /> },
  { header: "Control", cell: (row) => <Badge value={row.human_control} /> },
  { header: "Decided by", cell: (row) => enumLabel(row.decided_by) },
  { header: "Hours / month", cell: (row) => number(row.monthly_hours), className: "tabular-nums" },
  { header: "Score", cell: (row) => score(row.suitability_score), className: "tabular-nums" },
  { header: "Rationale", cell: (row) => row.rationale },
];

function ProcessSummary({ summary }: { summary: Blueprint["process_summary"] }) {
  const fact = (key: string) => String(summary[key] ?? "");
  const rows: readonly (readonly [string, string])[] = [
    ["Owner", fact("owner") || "None"],
    ["Executions per month", fact("executions_per_month")],
    ["Steps", fact("steps")],
    ["Process version", `v${fact("process_version")}`],
    ["Analysed", timestamp(fact("analysed_at"))],
    ["Rules", fact("rules_version")],
    ["LLM", fact("llm")],
  ];
  return (
    <Section n={1} title="Process summary">
      {fact("description") && <p className="mb-3 text-muted">{fact("description")}</p>}
      <dl className="m-0 grid grid-cols-[max-content_1fr] gap-x-6 gap-y-2 text-sm">
        {rows.map(([term, value]) => (
          <div key={term} className="contents">
            <dt className="text-muted">{term}</dt>
            <dd className="m-0 min-w-0 break-words">{value}</dd>
          </div>
        ))}
      </dl>
    </Section>
  );
}

function BusinessImpact({
  impact,
  stepNames,
}: {
  impact: Blueprint["business_impact"];
  stepNames: ReadonlyMap<string, string>;
}) {
  const { assumptions } = impact;
  const reductions = Object.entries(assumptions.expected_time_reduction_by_step ?? {}).map(
    ([stepId, value]) =>
      `Expected time reduction, ${stepNames.get(stepId) ?? shortId(stepId)}: ${percent(value)}`,
  );
  return (
    <Section n={5} title="Business impact">
      <dl className="mb-4 grid grid-cols-2 gap-2.5 xl:grid-cols-3">
        <MiniMetric term="Hours freed / month" value={hours(impact.estimated_hours_saved)} />
        <MiniMetric term="Net savings / month" value={money(impact.net_monthly_savings)} />
        <MiniMetric term="Payback" value={months(impact.payback_months)} />
        <MiniMetric term="ROI at 12 months" value={percent(impact.roi_12_months)} />
      </dl>
      <h3 id="blueprint-assumptions" className="mb-1.5 text-[15px] font-semibold">
        Assumptions
      </h3>
      <Bullets
        labelledBy="blueprint-assumptions"
        items={[
          `Implementation cost: ${money(assumptions.implementation_cost)}`,
          `Monthly tooling cost: ${money(assumptions.monthly_tooling_cost)}`,
          ...reductions,
        ]}
      />
    </Section>
  );
}

/** A numbered panel; its heading names the section for screen readers and the table. */
function Section({
  n,
  title,
  aside,
  children,
}: {
  n: number;
  title: string;
  aside?: ReactNode;
  children: ReactNode;
}) {
  return (
    <Panel id={`blueprint-${n}`} title={`${n}. ${title}`} action={aside} className="mb-6">
      {children}
    </Panel>
  );
}

/** The .mini-metrics card of web/styles.css: a smaller figure on the raised surface. */
function MiniMetric({ term, value }: { term: string; value: string }) {
  return (
    <div className="min-w-0 rounded-panel border border-line bg-surface-raised px-3.5 py-3">
      <dt className="text-xs text-muted">{term}</dt>
      <dd className="text-[19px] leading-snug font-semibold tracking-[-0.5px] break-words tabular-nums">
        {value}
      </dd>
    </div>
  );
}

/** The .bullets list of web/views.js, or a sentence when there is nothing to list. */
function Bullets({
  items,
  empty,
  labelledBy,
}: {
  items: readonly ReactNode[];
  empty?: string;
  labelledBy?: string;
}) {
  if (!items.length) return empty ? <p className="text-muted">{empty}</p> : null;
  return (
    <ul aria-labelledby={labelledBy} className="m-0 mb-3.5 list-none p-0">
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

/** The empty state of web/views.js: a quiet mark and a title. */
function Empty({ title }: { title: string }) {
  return (
    <div className="px-3 py-7 text-center">
      <span aria-hidden="true" className="mb-2 block text-[30px] text-muted">
        ◎
      </span>
      <h3 className="mb-1.5 text-[15px] font-semibold">{title}</h3>
    </div>
  );
}
