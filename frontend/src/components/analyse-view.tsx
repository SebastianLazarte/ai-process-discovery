"use client";

import { useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useRef, useState } from "react";
import { get, useForm, useWatch } from "react-hook-form";
import type { FieldPath } from "react-hook-form";

import { ApiError, applyFieldErrors } from "@/lib/api";
import { keys, useProcess, useRunAnalysis } from "@/lib/api/queries";
import type { ProcessRead } from "@/lib/api/queries";
import { percent } from "@/lib/format";

import { buttonClass } from "./button";
import { CheckboxField, NumberField } from "./field";
import { LlmWait } from "./llm-wait";
import type { WaitStatus } from "./llm-wait";
import { Panel } from "./panel";
import { useToast } from "./toast";

// RS-75: the Analyse tab, as analysePage in web/process-views.js. Inputs travel as strings
// and the API computes every figure (hard rule 7). Field names follow the API paths, so a
// 422 lands on its control through applyFieldErrors.
type Values = {
  implementation_cost: string;
  monthly_tooling_cost: string;
  expected_time_reduction_by_step: Record<string, string>;
  use_llm: boolean;
  confirm_sensitive: boolean;
};

// A gateway timeout or a lost connection may hide a run the API still finishes.
const MAYBE_RUNNING = new Set([0, 504]);

export function AnalyseView({ id }: { id: string }) {
  const process = useProcess(id);
  if (!process.data) return null;
  if (process.data.steps.length === 0)
    return (
      <Panel id="analyse-title" title="Analyse">
        <div className="py-8 text-center">
          <span aria-hidden="true">◎</span>
          <h3 className="font-semibold">No steps to analyse</h3>
          <p className="text-[13px] text-muted">
            Add steps on the <Link href={`/processes/${id}`}>Steps</Link> tab first.
          </p>
        </div>
      </Panel>
    );
  return <AnalyseForm process={process.data} />;
}

function AnalyseForm({ process }: { process: ProcessRead }) {
  const router = useRouter();
  const toast = useToast();
  const client = useQueryClient();
  const run = useRunAnalysis(process.id);
  const inFlight = useRef(false);
  const [startedAt, setStartedAt] = useState<number | null>(null);
  const [withLlm, setWithLlm] = useState(false);
  const [formError, setFormError] = useState<string[]>([]);
  const {
    register,
    handleSubmit,
    setError,
    control,
    formState: { errors },
  } = useForm<Values>({
    defaultValues: {
      implementation_cost: "",
      monthly_tooling_cost: "0",
      expected_time_reduction_by_step: Object.fromEntries(process.steps.map((s) => [s.id, "0"])),
      use_llm: false,
      confirm_sensitive: false,
    },
  });

  const sensitive = process.steps.filter((s) => s.handles_sensitive_data).map((s) => s.name);
  const [useLlm, confirmed, reductions] = useWatch({
    control,
    name: ["use_llm", "confirm_sensitive", "expected_time_reduction_by_step"],
  });
  const canRun = !run.isPending && (!useLlm || confirmed || sensitive.length === 0);

  const fields: FieldPath<Values>[] = [
    "implementation_cost",
    "monthly_tooling_cost",
    ...process.steps.map((s) => `expected_time_reduction_by_step.${s.id}` as FieldPath<Values>),
  ];

  const runAnalysis = (values: Values) => {
    // A second click before the first answer would run, and with the LLM pay for, a second
    // analysis: the ref closes the gap before the button disables.
    if (inFlight.current) return;
    inFlight.current = true;
    setFormError([]);
    setWithLlm(values.use_llm);
    setStartedAt(Date.now());
    const chosen = Object.entries(values.expected_time_reduction_by_step).filter(
      ([, value]) => value !== "0",
    );
    run.mutate(
      {
        use_llm: values.use_llm,
        confirm_sensitive: values.use_llm && values.confirm_sensitive,
        assumptions: {
          implementation_cost: values.implementation_cost.trim() || null,
          monthly_tooling_cost: values.monthly_tooling_cost.trim() || "0",
          expected_time_reduction_by_step: Object.fromEntries(chosen),
        },
      },
      {
        onSuccess: (analysis) => {
          toast(
            analysis.llm.status === "unavailable"
              ? "Saved without the LLM: it was unavailable."
              : "Analysis saved.",
          );
          router.push(`/processes/${process.id}/analyses/${analysis.id}`);
        },
        onError: (error) => {
          if (error instanceof ApiError && error.isFieldError)
            setFormError(applyFieldErrors(error, setError, fields));
          // 409: a step became sensitive since the page loaded; reload it to show the notice.
          if (error instanceof ApiError && error.status === 409)
            void client.invalidateQueries({ queryKey: keys.process(process.id), exact: true });
        },
        onSettled: () => {
          inFlight.current = false;
        },
      },
    );
  };

  const failure = run.error instanceof ApiError && !run.error.isFieldError ? run.error : null;
  const status: WaitStatus =
    withLlm && run.isPending ? "running" : withLlm && failure ? "failed" : "idle";
  const error = (name: FieldPath<Values>): string | undefined => get(errors, name)?.message;

  return (
    <Panel id="analyse-title" title="Analyse">
      <form
        onSubmit={(event) => handleSubmit(runAnalysis)(event)}
        noValidate
        className="grid gap-4 sm:grid-cols-2"
      >
        <p className="text-[13px] text-ink sm:col-span-2">
          Economic inputs are your assumptions. The system never estimates them and the LLM never
          sees them.
        </p>
        <NumberField
          id="implementation_cost"
          label="Implementation cost"
          hint="Leave empty if unknown."
          error={error("implementation_cost")}
          register={register("implementation_cost")}
        />
        <NumberField
          id="monthly_tooling_cost"
          label="Monthly tooling cost"
          error={error("monthly_tooling_cost")}
          register={register("monthly_tooling_cost")}
        />
        <fieldset className="min-w-0 rounded-[10px] border border-line px-4 pt-3.5 pb-1.5 sm:col-span-2">
          <legend className="px-1.5 text-xs text-muted">Expected time reduction per step</legend>
          {process.steps.map((s) => {
            const name = `expected_time_reduction_by_step.${s.id}` as const;
            return (
              <div key={s.id} className="mb-2.5">
                <label htmlFor={`reduction-${s.id}`} className="block text-[13px] text-label">
                  {s.position}. {s.name}
                </label>
                <div className="grid grid-cols-[1fr_52px] items-center gap-3">
                  <input
                    id={`reduction-${s.id}`}
                    type="range"
                    min="0"
                    max="1"
                    step="0.05"
                    className="min-h-7 accent-accent"
                    aria-invalid={error(name) ? true : undefined}
                    {...register(name)}
                  />
                  <output htmlFor={`reduction-${s.id}`} className="text-right text-[13px] text-ink">
                    {percent(reductions[s.id] ?? "0")}
                  </output>
                </div>
                {error(name) && <p className="mt-1 text-xs text-bad">{error(name)}</p>}
              </div>
            );
          })}
        </fieldset>
        <CheckboxField
          id="use_llm"
          label="Enrich with the LLM: interpretation, risks and architecture"
          wide
          register={register("use_llm")}
        />
        {/* Kept mounted and hidden, as in web/, so the confirmation survives a toggle. */}
        <div className="sm:col-span-2" hidden={!useLlm || sensitive.length === 0}>
          <p className="mb-2 rounded-r-lg border-l-[3px] border-bad bg-bad-bg px-4 py-3 text-[13px] text-ink">
            These steps handle sensitive data and their descriptions would be sent to the LLM
            provider: {sensitive.join(", ")}.
          </p>
          <CheckboxField
            id="confirm_sensitive"
            label="I confirm these descriptions can be sent to the provider"
            register={register("confirm_sensitive")}
          />
        </div>
        <LlmWait processId={process.id} status={status} startedAt={startedAt} />
        {failure && !run.isPending && (
          <div className="rounded-r-lg border-l-[3px] border-bad bg-bad-bg px-4 py-3 text-[13px] text-ink sm:col-span-2">
            <p>The analysis did not run: {failure.message}</p>
            {MAYBE_RUNNING.has(failure.status) && (
              <p className="mt-1">
                It may still finish on the server. Check the{" "}
                <Link href={`/processes/${process.id}/history`}>History</Link> before you run it
                again.
              </p>
            )}
            <p className="mt-1">Your values are kept.</p>
            <button type="submit" className={`${buttonClass("secondary")} mt-2`} disabled={!canRun}>
              Try again
            </button>
          </div>
        )}
        {formError.length > 0 && (
          <p role="alert" className="text-[13px] whitespace-pre-line text-bad sm:col-span-2">
            {formError.join(" ")}
          </p>
        )}
        <div className="sm:col-span-2">
          <button type="submit" className={buttonClass("primary")} disabled={!canRun}>
            {run.isPending ? "Running…" : "Run analysis"}
          </button>
        </div>
      </form>
    </Panel>
  );
}
