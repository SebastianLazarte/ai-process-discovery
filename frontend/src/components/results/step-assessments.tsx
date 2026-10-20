import type { AnalysisRead } from "@/lib/api/queries";
import { count, detail, enumLabel, hours, percent } from "@/lib/format";

import { Badge } from "../badge";
import { Note } from "./note";
import { SourceBadge } from "./source-badge";

// The step-by-step assessments, as stepDetail in web/analysis-views.js: the final decision
// with who made it, then the rules and the AI suggestion side by side. Badges sit in their
// own group and never on a figure. The override form arrives with RS-76.

type Step = AnalysisRead["step_assessments"][number];

const H4 = "mb-2.5 text-xs font-semibold tracking-[1.4px] text-muted uppercase";

function RulesColumn({ step }: { step: Step }) {
  return (
    <div className="min-w-0 text-[13px] text-muted">
      <h4 className={H4}>Rules</h4>
      <p className="mb-3">
        <Badge value={step.rules_method} /> {step.rules_method_reason}
      </p>
      <div className="overflow-x-auto">
        <table aria-label={`${step.name} score factors`} className="mb-3 w-full text-[13px]">
          <thead>
            <tr>
              {["Factor", "Points", "Detail"].map((title) => (
                <th
                  key={title}
                  scope="col"
                  className="border-b border-line px-2.5 py-2.5 text-left text-[10px] font-medium tracking-[1px] text-table-head uppercase"
                >
                  {title}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {step.score_factors.map((factor) => (
              <tr key={factor.name}>
                <td className="border-b border-line-soft px-2.5 py-3">{enumLabel(factor.name)}</td>
                <td className="border-b border-line-soft px-2.5 py-3 tabular-nums">
                  {count(factor.points)} / {count(factor.max_points)}
                </td>
                <td className="border-b border-line-soft px-2.5 py-3">{detail(factor.detail)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {step.score_penalties.length > 0 && (
        <p className="mb-3">
          <b>Penalties:</b>{" "}
          {step.score_penalties
            .map((penalty) => `${enumLabel(penalty.name)} (-${count(penalty.points)})`)
            .join(", ")}
        </p>
      )}
      {step.score_unknowns.length > 0 && (
        <p className="mb-3">
          <b>Unknown inputs:</b> {step.score_unknowns.map(enumLabel).join(", ")}
        </p>
      )}
    </div>
  );
}

function AiColumn({ step }: { step: Step }) {
  const ai = step.ai_suggestion;
  const extras = ai
    ? (
        [
          ["Dependencies", ai.dependencies],
          ["Risks", ai.risks],
          ["Uncertainties", ai.uncertainties],
        ] as const
      ).filter(([, items]) => items.length > 0)
    : [];
  return (
    <div className="min-w-0 text-[13px] text-muted">
      <h4 className={H4}>AI suggestion</h4>
      {ai ? (
        <>
          <p className="mb-3">
            <Badge value={ai.method} /> confidence {percent(ai.confidence)}
          </p>
          <p className="mb-3">{ai.interpretation}</p>
          <p className="mb-3 text-xs">{ai.rationale}</p>
          {extras.map(([title, items]) => (
            <p key={title} className="mb-3">
              <b>{title}:</b> {items.join("; ")}
            </p>
          ))}
        </>
      ) : (
        <p className="mb-3">No AI suggestion for this analysis.</p>
      )}
      {step.reconciliation_notes.map((text) => (
        <p key={text} className="mb-3 text-xs">
          Reconciliation: {text}
        </p>
      ))}
      {step.override && (
        <Note tone="info">
          Overridden from {enumLabel(step.override.original_method)} /{" "}
          {enumLabel(step.override.original_human_control)}: {step.override.reason}
        </Note>
      )}
    </div>
  );
}

function StepDetail({ step }: { step: Step }) {
  return (
    <details className="group border-t border-line first-of-type:border-t-0">
      <summary className="grid cursor-pointer list-none grid-cols-[28px_minmax(0,1fr)] items-center gap-3 px-1 py-3.5 group-open:border-b group-open:border-dashed group-open:border-line md:grid-cols-[36px_minmax(0,1fr)_auto_auto] [&::-webkit-details-marker]:hidden">
        <span className="pt-0.5 font-mono text-[13px] text-accent">
          {String(step.position).padStart(2, "0")}
        </span>
        <span className="font-semibold">{step.name}</span>
        <span
          aria-label="Decision"
          className="col-start-2 flex flex-wrap gap-1.5 md:col-start-auto"
        >
          <Badge value={step.final_method} />
          <Badge value={step.final_human_control}>
            Control: {enumLabel(step.final_human_control)}
          </Badge>
          <SourceBadge source={step.final_source} />
        </span>
        <span className="col-start-2 text-[13px] whitespace-nowrap text-muted tabular-nums md:col-start-auto">
          {hours(step.monthly_hours)}
        </span>
      </summary>
      <div className="grid gap-7 px-1 py-[18px] md:grid-cols-2">
        <RulesColumn step={step} />
        <AiColumn step={step} />
      </div>
    </details>
  );
}

export function StepAssessments({ analysis }: { analysis: AnalysisRead }) {
  return (
    <div>
      {analysis.step_assessments.map((step) => (
        <StepDetail key={step.step_id} step={step} />
      ))}
    </div>
  );
}
