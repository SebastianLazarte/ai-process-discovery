"use client";

import { ApiError } from "@/lib/api";
import { useAnalysis, useProcess } from "@/lib/api/queries";
import { hours, money } from "@/lib/format";

import { Metric, Metrics } from "./metric";
import { Panel } from "./panel";
import { ControlsPanel, ImpactPanel, Quads, RiskPanel, SuitabilityPanel } from "./results/panels";
import { ProvenanceBar } from "./results/provenance";
import { NO_HOURLY_COST, unknownNote } from "./results/reasons";
import { StepAssessments } from "./results/step-assessments";

// The Results tab (RS-92), as resultsPage in web/analysis-views.js: provenance, the current
// state, the four panels and the step-by-step assessments. Every figure is the API's.
export function ResultsView({ id, analysisId }: { id: string; analysisId: string }) {
  const analysis = useAnalysis(analysisId);
  const process = useProcess(id);

  if (analysis.isPending)
    return <p className="py-24 text-center text-muted">Loading the analysis…</p>;
  if (analysis.isError) {
    const missing = analysis.error instanceof ApiError && analysis.error.status === 404;
    return (
      <p className="py-24 text-center text-muted">
        {missing ? "This analysis does not exist." : "The analysis could not be loaded."}
      </p>
    );
  }

  const data = analysis.data;
  const stepNames = Object.fromEntries(
    (process.data?.steps ?? []).map((step) => [step.id, step.name]),
  );
  return (
    <>
      <ProvenanceBar analysis={data} />
      <section aria-label="Current state">
        <Metrics className="md:grid-cols-2 xl:grid-cols-2">
          <Metric term="Current monthly hours" value={hours(data.current_state.monthly_hours)} />
          <Metric
            term="Current monthly cost"
            value={money(data.current_state.monthly_cost)}
            note={unknownNote(data.current_state.monthly_cost, NO_HOURLY_COST)}
          />
        </Metrics>
      </section>
      <Quads>
        <SuitabilityPanel analysis={data} />
        <ImpactPanel analysis={data} stepNames={stepNames} />
        <RiskPanel analysis={data} />
        <ControlsPanel analysis={data} />
      </Quads>
      <Panel
        id="steps-title"
        title="Step by step"
        className="mt-6"
        action={
          <small className="text-xs text-muted">
            Open a step to see the rules and the AI suggestion.
          </small>
        }
      >
        <StepAssessments analysis={data} />
      </Panel>
    </>
  );
}
