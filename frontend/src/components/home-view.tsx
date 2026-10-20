"use client";

import { useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import { useRouter } from "next/navigation";

import { api, unwrap } from "@/lib/api";
import type { components } from "@/lib/api";
import { keys, useDemos, useLoadDemo, useProcesses } from "@/lib/api/queries";
import { count, timestamp, version } from "@/lib/format";

import { buttonClass } from "./button";
import { DataTable, SkeletonRows } from "./data-table";
import type { Column } from "./data-table";
import { Eyebrow, Panel } from "./panel";
import { ProcessForm } from "./process-form";

// Home (RS-73), laid out as the home of the vanilla client: the promise, the demos, then
// the creation form beside the process table.
export function HomeView() {
  return (
    <>
      <header className="mb-6">
        <Eyebrow>AI Process Discovery</Eyebrow>
        <h1 className="mb-3 text-[27px] leading-[1.15] font-semibold tracking-[-1.1px] md:text-[34px]">
          Map a process.
          <br />
          Get numbers you can defend.
        </h1>
        <p className="max-w-[760px] text-[15px] text-muted">
          Describe the steps, and the rules engine computes hours, cost, suitability and payback.
          The LLM only adds interpretation, and it can raise a human control but never remove one.
        </p>
      </header>
      <Demos />
      <div className="mt-6 grid items-start gap-6 xl:grid-cols-[1fr_1.3fr]">
        <Panel id="new-process-title" title="New process">
          <ProcessForm />
        </Panel>
        <Processes />
      </div>
    </>
  );
}

function Demos() {
  const demos = useDemos();
  const load = useLoadDemo();
  const router = useRouter();
  const client = useQueryClient();

  // A demo with preset assumptions comes with its first analysis (RS-89): open its results,
  // as web/ does. The list lands in the cache the process tabs read.
  async function open(processId: string) {
    const first = await client
      .fetchQuery({
        queryKey: keys.analyses(processId),
        queryFn: () =>
          unwrap(
            api.GET("/processes/{process_id}/analyses", {
              params: { path: { process_id: processId } },
            }),
          ),
      })
      .then(
        (analyses) => analyses[0],
        () => undefined,
      );
    router.push(first ? `/processes/${processId}/analyses/${first.id}` : `/processes/${processId}`);
  }

  return (
    <Panel id="demos-title" title="Start from a demo">
      {demos.isPending && <p className="text-sm text-muted">Loading demos…</p>}
      {demos.isError && <p className="text-sm text-muted">Demos are not available right now.</p>}
      <ul aria-labelledby="demos-title" className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {demos.data?.map((demo) => {
          const loading = load.isPending && load.variables === demo.slug;
          return (
            <li
              key={demo.slug}
              className="flex flex-col rounded-card border border-line bg-surface-raised p-[18px]"
            >
              <h3 className="mb-1.5 text-[15px] font-semibold">{demo.name}</h3>
              <p className="mb-4 flex-1 text-[13px] text-muted">{demo.description}</p>
              <button
                type="button"
                className={`${buttonClass("secondary")} self-start`}
                disabled={loading}
                onClick={() =>
                  load.mutate(demo.slug, {
                    onSuccess: (process) => open(process.id),
                  })
                }
              >
                {loading ? "Loading…" : "Load and open"}
                <span className="sr-only">: {demo.name}</span>
              </button>
            </li>
          );
        })}
      </ul>
    </Panel>
  );
}

type Row = components["schemas"]["ProcessSummary"];

const COLUMNS: readonly Column<Row>[] = [
  {
    header: "Process",
    cell: (process) => (
      <>
        <Link href={`/processes/${process.id}`} className="font-semibold">
          {process.name}
        </Link>
        <span className="mt-0.5 block text-xs text-muted">{process.owner ?? "No owner"}</span>
      </>
    ),
  },
  { header: "Runs / month", numeric: true, cell: (process) => count(process.executions_per_month) },
  { header: "Steps", numeric: true, cell: (process) => count(process.step_count) },
  { header: "Version", cell: (process) => version(process.version) },
  {
    header: "Updated",
    className: "whitespace-nowrap tabular-nums",
    cell: (process) => timestamp(process.updated_at),
  },
];

function Processes() {
  const processes = useProcesses();

  return (
    <Panel id="processes-title" title="Your processes">
      {processes.isPending && <SkeletonRows />}
      {processes.isError && (
        <p className="text-sm text-muted">
          The processes could not be loaded.{" "}
          <button
            type="button"
            className="text-accent underline"
            onClick={() => processes.refetch()}
          >
            Try again
          </button>
        </p>
      )}
      {processes.data?.length === 0 && (
        <p className="py-7 text-center text-[13px] text-muted">
          No processes yet. Load a demo or create one.
        </p>
      )}
      {processes.data && processes.data.length > 0 && (
        <DataTable
          labelledBy="processes-title"
          columns={COLUMNS}
          rows={processes.data}
          rowKey={(process) => process.id}
        />
      )}
    </Panel>
  );
}
