"use client";

import { useState } from "react";
import { useForm } from "react-hook-form";
import type { FieldPath } from "react-hook-form";

import { ApiError, applyFieldErrors } from "@/lib/api";
import { useAddOverride } from "@/lib/api/queries";
import type { AnalysisRead } from "@/lib/api/queries";
import { AUTOMATION_METHODS, HUMAN_CONTROLS } from "@/lib/format/options";
import type { AutomationMethod, HumanControl } from "@/lib/format/options";

import { SelectField, TextField } from "../field";
import { Submit } from "../process-form";
import { useToast } from "../toast";

type Step = AnalysisRead["step_assessments"][number];

// Selects keep a value the option lists do not name (RS-58), so they are plain strings here.
type Values = { method: string; human_control: string; reason: string };

const FIELDS: FieldPath<Values>[] = ["method", "human_control", "reason"];

const toValues = (step: Step): Values => ({
  method: step.final_method,
  human_control: step.final_human_control,
  reason: "",
});

/**
 * Overrides the method and human control of one step with a required reason, as
 * overrideForm in web/analysis-views.js (RS-76). A reason left empty is marked and nothing
 * is sent. The API keeps the original recommendation; the step shows both once saved.
 */
export function OverrideForm({ analysisId, step }: { analysisId: string; step: Step }) {
  const add = useAddOverride(analysisId);
  const toast = useToast();
  const [formError, setFormError] = useState<string[]>([]);
  const {
    register,
    handleSubmit,
    setError,
    reset,
    formState: { errors },
  } = useForm<Values>({ defaultValues: toValues(step) });

  const submit = handleSubmit((values) => {
    setFormError([]);
    add.mutate(
      {
        step_id: step.step_id,
        // A value the client does not list goes back as it came, so the casts only widen.
        method: values.method as AutomationMethod,
        human_control: values.human_control as HumanControl,
        reason: values.reason.trim(),
      },
      {
        onSuccess: (analysis) => {
          toast("Override saved. The original recommendation is kept.");
          const saved = analysis.step_assessments.find((item) => item.step_id === step.step_id);
          reset(toValues(saved ?? step));
        },
        onError: (error) => {
          if (error instanceof ApiError && error.isFieldError)
            setFormError(applyFieldErrors(error, setError, FIELDS));
        },
      },
    );
  });

  const field = (name: FieldPath<Values>) => ({
    id: `override-${step.step_id}-${name}`,
    error: errors[name]?.message,
    register: register(
      name,
      name === "reason"
        ? {
            validate: (value) =>
              value.trim().length >= 3 || "Give a reason of at least 3 characters.",
          }
        : undefined,
    ),
  });

  return (
    <section
      aria-label={`Override ${step.name}`}
      className="mx-1 mb-[18px] rounded-[10px] bg-surface-raised p-4"
    >
      <h4 className="mb-2.5 text-xs font-semibold tracking-[1.4px] text-muted uppercase">
        Override this recommendation
      </h4>
      <form onSubmit={submit} noValidate>
        <div className="mb-2.5 grid gap-4 md:grid-cols-[1fr_1fr_2fr]">
          <SelectField
            label="Method"
            options={AUTOMATION_METHODS}
            current={step.final_method}
            {...field("method")}
          />
          <SelectField
            label="Human control"
            options={HUMAN_CONTROLS}
            current={step.final_human_control}
            {...field("human_control")}
          />
          <TextField label="Reason" required {...field("reason")} />
        </div>
        <Submit
          formError={formError}
          pending={add.isPending}
          label="Save override"
          pendingLabel="Saving…"
        />
      </form>
    </section>
  );
}
