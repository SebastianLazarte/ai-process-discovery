"use client";

import type { ReactNode } from "react";

import { ApiError } from "@/lib/api";
import { useProcess } from "@/lib/api/queries";

import { Eyebrow } from "./panel";
import { ProcessHeader } from "./process-header";
import { ProcessTabs } from "./process-tabs";

// The frame of every process page (app/processes/[id]/layout.tsx): the title and the
// section tabs, then the section. A process that does not load shows why, and no section.
export function ProcessView({ id, children }: { id: string; children?: ReactNode }) {
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

  return (
    <>
      <ProcessHeader process={process.data} />
      <ProcessTabs processId={id} />
      {children}
    </>
  );
}
