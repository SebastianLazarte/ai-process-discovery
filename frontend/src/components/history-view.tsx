"use client";

import Link from "next/link";

import { useAnalyses } from "@/lib/api/queries";
import type { components } from "@/lib/api/schema";
import { count, shortId, timestamp, version } from "@/lib/format";

import { Badge } from "./badge";
import { buttonClass } from "./button";
import { DataTable, SkeletonRows, type Column } from "./data-table";
import { Panel } from "./panel";

// The History tab (RS-93), as historyPage in web/process-views.js: every analysis of the
// process in the order the API sends them, newest first, each one opening its Results.

type Row = components["schemas"]["AnalysisSummary"];

function columns(processId: string): readonly Column<Row>[] {
  return [
    {
      header: "Created",
      className: "whitespace-nowrap tabular-nums",
      cell: (row) => timestamp(row.created_at),
    },
    {
      header: "Id",
      cell: (row) => <code className="font-mono text-xs text-muted">{shortId(row.id)}</code>,
    },
    { header: "Process", cell: (row) => version(row.process_version) },
    { header: "Rules", cell: (row) => row.rules_version },
    { header: "LLM", cell: (row) => <Badge value={row.llm_status} /> },
    { header: "Overrides", numeric: true, cell: (row) => count(row.override_count) },
    {
      header: <span className="sr-only">Results</span>,
      cell: (row) => (
        <Link
          href={`/processes/${processId}/analyses/${row.id}`}
          aria-label={`Open analysis ${shortId(row.id)}`}
          className={buttonClass("secondary")}
        >
          Open
        </Link>
      ),
    },
  ];
}

export function HistoryView({ id }: { id: string }) {
  const analyses = useAnalyses(id);

  return (
    <Panel id="history-title" title="Analysis history">
      <p className="mb-4 text-[13px] text-muted">
        Each analysis is an immutable snapshot. Results differ when the process version, the rules
        version or the LLM changed.
      </p>
      {analyses.isPending && <SkeletonRows />}
      {analyses.isError && (
        <p className="text-sm text-muted">
          The analyses could not be loaded.{" "}
          <button
            type="button"
            className="text-accent underline"
            onClick={() => analyses.refetch()}
          >
            Try again
          </button>
        </p>
      )}
      {analyses.data?.length === 0 && (
        <div className="px-3 py-7 text-center">
          <span aria-hidden="true" className="mb-2 block text-[30px] text-muted">
            ◎
          </span>
          <h3 className="text-[15px] font-semibold">No analyses yet</h3>
          <p className="mx-auto mt-1 max-w-[360px] text-[13px] text-muted">
            Run one from the <Link href={`/processes/${id}/analyse`}>Analyse</Link> tab.
          </p>
        </div>
      )}
      {analyses.data && analyses.data.length > 0 && (
        <DataTable
          labelledBy="history-title"
          columns={columns(id)}
          rows={analyses.data}
          rowKey={(row) => row.id}
        />
      )}
    </Panel>
  );
}
