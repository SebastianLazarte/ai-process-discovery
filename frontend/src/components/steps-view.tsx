"use client";

import { useRouter } from "next/navigation";

import { useDeleteProcess, useProcess } from "@/lib/api/queries";
import { count, money } from "@/lib/format";

import { ConfirmButton } from "./confirm-button";
import { Metric, Metrics } from "./metric";
import { Panel } from "./panel";
import { useToast } from "./toast";

// The Steps tab, where a process opens. Stub until RS-74 adds the step list and form; it
// keeps what the process page showed before: the facts of the process and its deletion.
export function StepsView({ id }: { id: string }) {
  const process = useProcess(id);
  if (!process.data) return null;

  const data = process.data;
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
      <Panel id="steps-title" title="Steps" className="mb-6">
        <p className="text-[13px] text-muted">
          The step editor arrives with the next release of this client.
        </p>
      </Panel>
      <DeleteProcess id={data.id} name={data.name} />
    </>
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
