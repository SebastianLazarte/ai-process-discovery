"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import type { AnalysisRead } from "@/lib/api/queries";
import { enumLabel } from "@/lib/format";

// RS-75: the honest wait. The API reports no progress, so the expected wait comes from the
// API configuration (src/app/core/config.py): LLM_TIMEOUT_SECONDS times 1 + LLM_MAX_RETRIES,
// the same bound that sets proxy_read_timeout in deploy/nginx/apd-routes.conf.
const LLM_TIMEOUT_SECONDS = 60;
const LLM_MAX_RETRIES = 2;
export const EXPECTED_WAIT_SECONDS = LLM_TIMEOUT_SECONDS * (1 + LLM_MAX_RETRIES);
export const REMINDER_SECONDS = 30;

export type WaitStatus = "idle" | "running" | "failed";

/** 0:45, 3:00: a duration for the visible clock. */
function clock(seconds: number): string {
  return `${Math.floor(seconds / 60)}:${String(seconds % 60).padStart(2, "0")}`;
}

/** 30 seconds, 1 min 30 s: a duration for a sentence. */
function spoken(seconds: number): string {
  const minutes = Math.floor(seconds / 60);
  const rest = seconds % 60;
  if (minutes === 0) return `${rest} seconds`;
  return rest === 0 ? `${minutes} min` : `${minutes} min ${rest} s`;
}

export const START_MESSAGE = `Analysis started. With the AI it can take up to ${spoken(EXPECTED_WAIT_SECONDS)}.`;
export const FAILED_MESSAGE = "The run ended without an analysis. Your values are kept.";

/**
 * The wait of a run with the LLM: an indeterminate indicator, the elapsed time and the
 * expected wait. The polite live region stays mounted, so it announces the start, at most one
 * reminder every 30 seconds and a failure; a success is announced by the toast, which
 * outlives the navigation to the results.
 */
export function LlmWait({
  processId,
  status,
  startedAt,
}: {
  processId: string;
  status: WaitStatus;
  /** Date.now() when the run started, set by the submit handler. */
  startedAt: number | null;
}) {
  const [now, setNow] = useState(0);
  const running = status === "running" && startedAt !== null;

  useEffect(() => {
    if (!running) return;
    const timer = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(timer);
  }, [running]);

  const elapsed = running ? Math.max(0, Math.floor((now - startedAt) / 1000)) : 0;
  const reminders = Math.floor(elapsed / REMINDER_SECONDS);
  const message = running
    ? reminders > 0
      ? `Still running: ${spoken(reminders * REMINDER_SECONDS)} elapsed.`
      : START_MESSAGE
    : status === "failed"
      ? FAILED_MESSAGE
      : "";

  return (
    <div className="sm:col-span-2">
      <p role="status" aria-live="polite" className="sr-only">
        {message}
      </p>
      {running && (
        <div className="rounded-r-lg border-l-[3px] border-info bg-info-bg px-4 py-3 text-[13px] text-ink">
          <progress aria-label="Running the analysis" className="mb-2 block w-full accent-accent" />
          <p>
            Elapsed <span role="timer">{clock(elapsed)}</span> · expected wait up to{" "}
            {spoken(EXPECTED_WAIT_SECONDS)}.
          </p>
          {elapsed > EXPECTED_WAIT_SECONDS && (
            <p className="mt-1">
              This is taking longer than expected. If it fails, check the History before you try
              again.
            </p>
          )}
          <p className="mt-1">
            Leaving this page does not cancel the run: the analysis will appear in the{" "}
            <Link href={`/processes/${processId}/history`}>History</Link>.
          </p>
        </div>
      )}
    </div>
  );
}

/** RS-75: on the results, why the AI part is missing. The deterministic part never is. */
export function LlmUnavailableNote({ llm }: { llm: AnalysisRead["llm"] }) {
  if (llm.status !== "unavailable") return null;
  return (
    <p
      role="note"
      className="mb-4 rounded-r-lg border-l-[3px] border-warn bg-warn-bg px-4 py-3 text-[13px] text-warn-ink"
    >
      {llm.error_kind === "daily_quota"
        ? "Today's AI quota of this demo is used up, so the LLM was skipped. The deterministic results are complete."
        : `The LLM was unavailable (${enumLabel(llm.error_kind ?? "error")}). The deterministic results are complete.`}
    </p>
  );
}
