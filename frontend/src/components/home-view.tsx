"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";

import { useDemos, useLoadDemo, useProcesses } from "@/lib/api/queries";
import { count, steps, timestamp, version } from "@/lib/format";

import { buttonClass } from "./button";

// Home (RS-73), alternative C of docs/design/02-ia-wireframes.md: demos first with one-click
// loading, then the process list; the creation form lives on its own page.
export function HomeView() {
  return (
    <>
      <header className="max-w-2xl">
        <h1 className="text-3xl font-semibold tracking-tight">
          Map a process. Get numbers you can defend.
        </h1>
        <p className="mt-3 text-gray-700">
          Rules compute every hour and cost. The AI only interprets.
        </p>
      </header>
      <Demos />
      <Processes />
    </>
  );
}

function Demos() {
  const demos = useDemos();
  const load = useLoadDemo();
  const router = useRouter();

  return (
    <section aria-labelledby="demos-title" className="mt-10">
      <h2 id="demos-title" className="text-lg font-semibold">
        Try a demo
      </h2>
      {demos.isPending && <p className="mt-3 text-gray-600">Loading demos…</p>}
      {demos.isError && <p className="mt-3 text-gray-600">Demos are not available right now.</p>}
      <ul aria-labelledby="demos-title" className="mt-4 grid gap-4 md:grid-cols-3">
        {demos.data?.map((demo) => {
          const loading = load.isPending && load.variables === demo.slug;
          return (
            <li key={demo.slug} className="flex flex-col rounded-lg border border-gray-200 p-4">
              <h3 className="font-medium">{demo.name}</h3>
              <p className="mt-2 line-clamp-3 flex-1 text-sm text-gray-700">{demo.description}</p>
              <button
                type="button"
                className={`${buttonClass("secondary")} mt-4`}
                disabled={loading}
                onClick={() =>
                  load.mutate(demo.slug, {
                    onSuccess: (process) => router.push(`/processes/${process.id}`),
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
    </section>
  );
}

function Processes() {
  const processes = useProcesses();

  return (
    <section aria-labelledby="processes-title" className="mt-12">
      <div className="flex items-center justify-between gap-4">
        <h2 id="processes-title" className="text-lg font-semibold">
          Processes
        </h2>
        <Link href="/processes/new" className={buttonClass("secondary")}>
          New process
        </Link>
      </div>
      {processes.isPending && <SkeletonRows />}
      {processes.isError && (
        <p className="mt-4 text-gray-700">
          The processes could not be loaded.{" "}
          <button type="button" className="underline" onClick={() => processes.refetch()}>
            Try again
          </button>
        </p>
      )}
      {processes.data?.length === 0 && (
        <p className="mt-4 text-gray-700">No processes yet. Load a demo or create one.</p>
      )}
      {processes.data && processes.data.length > 0 && (
        <ul
          aria-labelledby="processes-title"
          className="mt-4 divide-y divide-gray-200 rounded-lg border border-gray-200"
        >
          {processes.data.map((process) => (
            <li key={process.id}>
              <Link
                href={`/processes/${process.id}`}
                className="grid min-h-11 gap-1 px-4 py-3 no-underline hover:bg-gray-50 md:grid-cols-[1fr_auto]"
              >
                <span>
                  <span className="font-medium underline">{process.name}</span>
                  <span className="block text-sm text-gray-600">{process.owner ?? "No owner"}</span>
                </span>
                <span className="text-sm tabular-nums text-gray-600 md:text-right">
                  {count(process.executions_per_month)} runs/month · {steps(process.step_count)} ·{" "}
                  {version(process.version)} · {timestamp(process.updated_at)}
                </span>
              </Link>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

function SkeletonRows() {
  return (
    <ul aria-hidden="true" className="mt-4 space-y-3">
      {[0, 1, 2].map((row) => (
        <li
          key={row}
          className="h-14 animate-pulse rounded-lg bg-gray-100 motion-reduce:animate-none"
        />
      ))}
    </ul>
  );
}
