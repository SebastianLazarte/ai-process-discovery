"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { ApiError } from "@/lib/api";
import { useDeleteProcess, useProcess } from "@/lib/api/queries";
import { count, money, version } from "@/lib/format";

import { buttonClass } from "./button";
import { Eyebrow, Panel } from "./panel";
import { useToast } from "./toast";

// The page a process opens on, laid out as in the vanilla client. RS-74 adds the step
// editor; for now it shows the process and lets you delete it.
export function ProcessView({ id }: { id: string }) {
  const process = useProcess(id);

  if (process.isPending)
    return <p className="py-24 text-center text-muted">Loading the process…</p>;
  if (process.isError) {
    const missing = process.error instanceof ApiError && process.error.status === 404;
    return (
      <header>
        <Eyebrow>Process</Eyebrow>
        <h1 className="mb-3 text-[27px] font-semibold tracking-[-1.1px] md:text-[34px]">
          {missing ? "This process does not exist" : "The process could not be loaded"}
        </h1>
        {missing && (
          <p className="text-muted">It may have been deleted. Public demo data is deleted daily.</p>
        )}
      </header>
    );
  }

  const data = process.data;
  return (
    <>
      <header className="mb-6">
        <Eyebrow>Process · {version(data.version)}</Eyebrow>
        <h1 className="mb-3 text-[27px] leading-[1.15] font-semibold tracking-[-1.1px] md:text-[34px]">
          {data.name}
        </h1>
        {data.description && (
          <p className="max-w-[760px] text-[15px] text-muted">{data.description}</p>
        )}
      </header>
      <dl className="mb-6 grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <Metric term="Executions / month" value={count(data.executions_per_month)} />
        <Metric
          term="Hourly cost"
          value={money(data.hourly_cost)}
          note={data.hourly_cost === null ? "Costs stay unknown" : undefined}
        />
        <Metric term="Steps" value={count(data.steps.length)} />
        <Metric term="Owner" value={data.owner ?? "None"} />
      </dl>
      <Panel id="steps-title" title="Steps" className="mb-6">
        <p className="text-[13px] text-muted">
          The step editor arrives with the next release of this client.
        </p>
      </Panel>
      <DeleteProcess id={data.id} name={data.name} />
    </>
  );
}

function Metric({ term, value, note }: { term: string; value: string; note?: string }) {
  return (
    <div className="min-w-0 rounded-panel border border-line bg-surface px-5 py-[18px]">
      <dt className="text-xs text-muted">{term}</dt>
      <dd className="text-[26px] leading-snug font-semibold tracking-[-0.5px] break-words tabular-nums">
        {value}
      </dd>
      {note && <dd className="text-xs text-muted">{note}</dd>}
    </div>
  );
}

// Two steps instead of a browser confirm(): the second button names what goes, and focus
// stays in the page.
function DeleteProcess({ id, name }: { id: string; name: string }) {
  const [confirming, setConfirming] = useState(false);
  const remove = useDeleteProcess();
  const router = useRouter();
  const toast = useToast();

  if (!confirming) {
    return (
      <button type="button" className={buttonClass("danger")} onClick={() => setConfirming(true)}>
        Delete process
      </button>
    );
  }
  return (
    <div
      role="group"
      aria-labelledby="delete-title"
      className="max-w-xl rounded-r-control border-l-[3px] border-bad bg-bad-bg px-4 py-3"
    >
      <p id="delete-title" className="text-sm text-ink">
        Delete “{name}” and all its analyses? This cannot be undone.
      </p>
      <div className="mt-3 flex flex-wrap gap-3">
        <button
          type="button"
          className={buttonClass("danger")}
          disabled={remove.isPending}
          onClick={() =>
            remove.mutate(id, {
              onSuccess: () => {
                toast(`Deleted “${name}”.`);
                router.push("/");
              },
            })
          }
        >
          {remove.isPending ? "Deleting…" : "Delete for good"}
        </button>
        <button
          type="button"
          className={buttonClass("secondary")}
          onClick={() => setConfirming(false)}
        >
          Keep it
        </button>
      </div>
    </div>
  );
}
