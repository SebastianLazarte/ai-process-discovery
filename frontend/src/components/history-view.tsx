"use client";

import Link from "next/link";

import { useAnalyses } from "@/lib/api/queries";
import type { components } from "@/lib/api/schema";
import { count, shortId, timestamp, version } from "@/lib/format";

import { Badge } from "./badge";
import { Button, buttonClass } from "./button";
import { PlayIcon } from "./icons";
import { EmptyState } from "./states";
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
          <Button variant="tertiary" onClick={() => analyses.refetch()}>
            Try again
          </Button>
        </p>
      )}
      {analyses.data?.length === 0 && (
        <EmptyState
          title="No analyses yet"
          icon={<PlayIcon />}
          action={
            <Link href={`/processes/${id}/analyse`} className={buttonClass("secondary")}>
              Go to Analyse
            </Link>
          }
        >
          Each analysis you run is kept here as a snapshot.
        </EmptyState>
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
