"use client";

import { useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import { useRouter } from "next/navigation";

import { api, unwrap } from "@/lib/api";
import type { components } from "@/lib/api";
import { keys, useDemos, useLoadDemo, useMeta, useProcesses } from "@/lib/api/queries";
import { count, steps, timestamp, version } from "@/lib/format";

import { Badge } from "./badge";
import { Button, buttonClass } from "./button";
import { DataTable, SkeletonRows } from "./data-table";
import type { Column } from "./data-table";
import { DescribeIcon, PlayIcon, ProcessesIcon, TemplatesIcon } from "./icons";
import { Eyebrow, Panel } from "./panel";
import { DemoCardsSkeleton, EmptyState } from "./states";

// Home (RS-73, RS-106 on Graphite, ADR 0018): the promise, then three ways to start, the
// demos and the processes of this browser. The sidebar holds the one filled primary
// action, New process; the way that leads there, your sector, is the card set apart here.
export function HomeView() {
  return (
    <>
      <header className="mb-10">
        <Eyebrow>AI Process Discovery</Eyebrow>
        <h1 className="mb-4 text-[32px] leading-[1.08] font-semibold tracking-[-1.2px] md:text-display">
          Map a process.
          <br />
          <span className="text-accent">Get numbers you can defend.</span>
        </h1>
        <p className="max-w-[640px] text-base text-ink-soft md:text-[17px]">
          Rules compute every hour, cost and payback. The AI only interprets, and it can raise a
          human control but never remove one.
        </p>
      </header>
      <WaysToStart />
      <Demos />
      <div className="mt-6">
        <Processes />
      </div>
    </>
  );
}

const startCard =
  "flex h-full flex-col gap-2.5 rounded-panel bg-surface p-[22px] text-ink no-underline transition-colors duration-150 hover:bg-surface-raised hover:text-ink hover:no-underline focus-visible:outline-3 focus-visible:outline-offset-3 focus-visible:outline-accent";

/** Your sector, your own words (only while AI drafts are on), or a finished demo. */
function WaysToStart() {
  const meta = useMeta();
  const drafts = meta.data?.process_drafts_enabled === true;

  return (
    <section aria-labelledby="start-title" className="mb-10">
      <h2 id="start-title" className="sr-only">
        Ways to start
      </h2>
      <ul
        aria-labelledby="start-title"
        className={`grid gap-4 sm:grid-cols-2 ${drafts ? "lg:grid-cols-3" : ""}`}
      >
        <li>
          <Link href="/processes/new" className={`${startCard} ring-1 ring-accent/40 ring-inset`}>
            <TemplatesIcon className="size-[26px] text-accent" />
            <span className="text-[17px] font-semibold">Start from your sector</span>
            <span className="text-sm text-ink-soft">
              Common processes of your sector come with their steps filled in. You add the numbers
              of your company.
            </span>
          </Link>
        </li>
        {drafts && (
          <li>
            <Link href="/processes/new" className={startCard}>
              <DescribeIcon className="size-[26px] text-ai" />
              <span className="flex items-center gap-2 text-[17px] font-semibold">
                Describe it in your words <Badge value="AI" />
              </span>
              <span className="text-sm text-ink-soft">
                The AI drafts the steps. Nothing is saved until you confirm.
              </span>
            </Link>
          </li>
        )}
        <li>
          <Link href="#demos-title" className={startCard}>
            <PlayIcon className="size-[26px] text-muted" />
            <span className="text-[17px] font-semibold">Open a demo</span>
            <span className="text-sm text-ink-soft">
              A finished analysis in one click, with savings, payback and human controls.
            </span>
          </Link>
        </li>
      </ul>
    </section>
  );
}

/** The figures of a demo card, all counted by the API: none when it sends none. */
function demoFigures(demo: Demo): string[] {
  const figures: string[] = [];
  if (demo.step_count != null) figures.push(steps(demo.step_count));
  if (demo.executions_per_month != null) {
    figures.push(`${count(demo.executions_per_month)} runs a month`);
  }
  return figures;
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
    <Panel id="demos-title" title="Demos" className="scroll-mt-6">
      {demos.isPending && <DemoCardsSkeleton />}
      {demos.isError && <p className="text-sm text-muted">Demos are not available right now.</p>}
      {demos.data && (
        <ul aria-labelledby="demos-title" className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {demos.data?.map((demo) => {
            const loading = load.isPending && load.variables === demo.slug;
            const figures = demoFigures(demo);
            return (
              <li key={demo.slug} className="flex flex-col rounded-card bg-surface-raised p-5">
                <h3 className="mb-1 text-base font-semibold">{demo.name}</h3>
                {figures.length > 0 && (
                  <p className="mb-2 text-[13px] text-muted tabular-nums">{figures.join(" · ")}</p>
                )}
                <p className="mb-4 flex-1 text-[13px] text-ink-soft">{demo.description}</p>
                <Button
                  className="self-start"
                  pending={loading}
                  onClick={() =>
                    load.mutate(demo.slug, {
                      onSuccess: (process) => open(process.id),
                    })
                  }
                >
                  Load and open
                  <span className="sr-only">: {demo.name}</span>
                </Button>
              </li>
            );
          })}
        </ul>
      )}
    </Panel>
  );
}

type Demo = components["schemas"]["DemoSummary"];
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
          <Button variant="tertiary" onClick={() => processes.refetch()}>
            Try again
          </Button>
        </p>
      )}
      {processes.data?.length === 0 && (
        <EmptyState
          title="No processes yet"
          icon={<ProcessesIcon />}
          action={
            <>
              <Link href="/processes/new" className={buttonClass("secondary")}>
                Start from your sector
              </Link>
              <Link href="#demos-title" className={buttonClass("tertiary")}>
                Open a demo
              </Link>
            </>
          }
        >
          Load a demo or create one. It shows here with its runs, steps and version.
        </EmptyState>
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
