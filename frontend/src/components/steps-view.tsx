"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { useDeleteProcess, useProcess } from "@/lib/api/queries";
import type { ProcessRead } from "@/lib/api/queries";
import { count, enumLabel, money, number, percent } from "@/lib/format";

import { Badge } from "./badge";
import { buttonClass } from "./button";
import { ConfirmButton } from "./confirm-button";
import { Dialog } from "./dialog";
import { Metric, Metrics } from "./metric";
import { Panel } from "./panel";
import { ProcessSettingsForm } from "./process-form";
import { StepForm } from "./step-form";
import { useToast } from "./toast";

type Step = ProcessRead["steps"][number];

/** What the dialog edits: a new step, or a stored one. */
type Editing = { step?: Step } | null;

// The Steps tab, where a process opens, as stepsPage in web/process-views.js: the facts of
// the process, its steps in order with the form to add or edit one, and its settings.
// Reordering and deleting steps arrive with RS-91.
export function StepsView({ id }: { id: string }) {
  const process = useProcess(id);
  const [editing, setEditing] = useState<Editing>(null);
  if (!process.data) return null;

  const data = process.data;
  const close = () => setEditing(null);
  return (
    <>
      <Metrics>
        <Metric term="Executions / month" value={count(data.executions_per_month)} />
        <Metric
          term="Hourly cost"
          value={money(data.hourly_cost)}
          note={data.hourly_cost === null ? "Costs stay unknown" : undefined}
        />
        <Metric term="Steps" value={count(data.steps.length)} />
        <Metric term="Owner" value={data.owner ?? "None"} />
      </Metrics>
      <Panel
        id="steps-title"
        title="Steps"
        className="mb-6"
        action={
          <button type="button" className={buttonClass("primary")} onClick={() => setEditing({})}>
            Add step
          </button>
        }
      >
        {data.steps.length > 0 ? (
          <ol aria-labelledby="steps-title">
            {data.steps.map((step) => (
              <StepRow key={step.id} step={step} onEdit={() => setEditing({ step })} />
            ))}
          </ol>
        ) : (
          <div className="px-3 py-7 text-center">
            <span aria-hidden="true" className="mb-2 block text-[30px] text-muted">
              ◎
            </span>
            <h3 className="mb-1 text-[15px] font-semibold">No steps yet</h3>
            <p className="mx-auto max-w-[360px] text-[13px] text-muted">
              Add the first step to analyse this process.
            </p>
          </div>
        )}
      </Panel>
      <Panel
        id="settings-title"
        title="Process settings"
        action={<DeleteProcess id={data.id} name={data.name} />}
      >
        <ProcessSettingsForm process={data} />
      </Panel>
      <Dialog
        open={editing !== null}
        onClose={close}
        wide
        title={editing?.step ? `Edit step ${editing.step.position}` : "Add a step"}
      >
        {editing && (
          <StepForm
            key={editing.step?.id ?? "new"}
            processId={data.id}
            step={editing.step}
            onSaved={close}
          />
        )}
        <button type="button" className={`${buttonClass()} mt-2`} onClick={close}>
          Close
        </button>
      </Dialog>
    </>
  );
}

function StepRow({ step, onEdit }: { step: Step; onEdit: () => void }) {
  return (
    <li className="grid grid-cols-[28px_minmax(0,1fr)] items-start gap-3.5 border-t border-line py-4 first:border-t-0 first:pt-0 sm:grid-cols-[36px_minmax(0,1fr)_auto]">
      <span className="pt-0.5 font-mono text-[13px] text-accent">
        {String(step.position).padStart(2, "0")}
      </span>
      <div className="min-w-0">
        <h3 className="mb-0.5 text-[15px] font-semibold">{step.name}</h3>
        <p className="mb-2 text-[13px] text-muted">
          {step.responsible_role || "No role"} · {number(step.minutes_per_execution, 1)} min · runs
          in {percent(step.occurrence_rate)} of executions · exception rate{" "}
          {percent(step.exception_rate)}
        </p>
        <div className="flex flex-wrap gap-1.5">
          <Badge value={step.input_type} tone="neutral" />
          <Badge tone="neutral">Integration: {enumLabel(step.integration_readiness)}</Badge>
          <Badge tone="neutral">Rules: {enumLabel(step.rule_clarity)}</Badge>
          {step.requires_human_judgement && <Badge tone="warn">Human judgement</Badge>}
          {step.requires_human_approval && <Badge tone="warn">Approval</Badge>}
          {step.handles_sensitive_data && <Badge tone="bad">Sensitive data</Badge>}
        </div>
      </div>
      <div className="col-start-2 flex flex-wrap items-center gap-1.5 sm:col-start-auto sm:justify-end">
        <button
          type="button"
          className={buttonClass()}
          aria-label={`Edit ${step.name}`}
          onClick={onEdit}
        >
          Edit
        </button>
      </div>
    </li>
  );
}

function DeleteProcess({ id, name }: { id: string; name: string }) {
  const remove = useDeleteProcess();
  const router = useRouter();
  const toast = useToast();

  return (
    <ConfirmButton
      label="Delete process"
      question={`Delete “${name}” and all its analyses? This cannot be undone.`}
      confirmLabel="Delete for good"
      pendingLabel="Deleting…"
      pending={remove.isPending}
      onConfirm={() =>
        remove.mutate(id, {
          onSuccess: () => {
            toast(`Deleted “${name}”.`);
            router.push("/");
          },
        })
      }
    />
  );
}
