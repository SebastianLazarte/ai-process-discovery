"use client";

import { useState } from "react";
import { useForm } from "react-hook-form";
import type { FieldPath } from "react-hook-form";

import { ApiError, applyFieldErrors } from "@/lib/api";
import { useAddStep, useUpdateStep } from "@/lib/api/queries";
import type { ProcessRead, StepUpdate } from "@/lib/api/queries";
import { INPUT_TYPES, INTEGRATION_READINESS, LEVELS } from "@/lib/format/options";
import type { InputType, IntegrationReadiness, Level } from "@/lib/format/options";

import { CheckboxField, NumberField, SelectField, TextField } from "./field";
import { Submit } from "./process-form";
import { useToast } from "./toast";

type Step = ProcessRead["steps"][number];

// Values travel as typed; the API validates and converts them (hard rule 7). An empty
// exception rate is sent as null, meaning unknown, never as zero. Selects keep a stored
// value the option lists do not name (RS-58), so their values are plain strings here.
type Values = {
  name: string;
  responsible_role: string;
  description: string;
  minutes_per_execution: string;
  occurrence_rate: string;
  exception_rate: string;
  repetitiveness: string;
  rule_clarity: string;
  criticality: string;
  input_type: string;
  integration_readiness: string;
  tools: string;
  requires_human_judgement: boolean;
  requires_human_approval: boolean;
  handles_sensitive_data: boolean;
};

const FIELDS: FieldPath<Values>[] = [
  "name",
  "responsible_role",
  "description",
  "minutes_per_execution",
  "occurrence_rate",
  "exception_rate",
  "repetitiveness",
  "rule_clarity",
  "criticality",
  "input_type",
  "integration_readiness",
  "tools",
  "requires_human_judgement",
  "requires_human_approval",
  "handles_sensitive_data",
];

function toValues(step?: Step): Values {
  return {
    name: step?.name ?? "",
    responsible_role: step?.responsible_role ?? "",
    description: step?.description ?? "",
    minutes_per_execution: step?.minutes_per_execution ?? "5",
    occurrence_rate: step?.occurrence_rate ?? "1",
    exception_rate: step?.exception_rate ?? "",
    repetitiveness: step?.repetitiveness ?? "UNKNOWN",
    rule_clarity: step?.rule_clarity ?? "UNKNOWN",
    criticality: step?.criticality ?? "UNKNOWN",
    input_type: step?.input_type ?? "UNKNOWN",
    integration_readiness: step?.integration_readiness ?? "UNKNOWN",
    tools: (step?.tools ?? []).join(", "),
    requires_human_judgement: step?.requires_human_judgement ?? false,
    requires_human_approval: step?.requires_human_approval ?? false,
    handles_sensitive_data: step?.handles_sensitive_data ?? false,
  };
}

/** The fields this form owns, as stepPayload in web/app.js. */
function toBody(values: Values) {
  return {
    name: values.name.trim(),
    responsible_role: values.responsible_role.trim(),
    description: values.description.trim(),
    minutes_per_execution: values.minutes_per_execution.trim(),
    occurrence_rate: values.occurrence_rate.trim() || "1",
    exception_rate: values.exception_rate.trim() || null,
    // A value the client does not list goes back as it came, so the casts only widen.
    repetitiveness: values.repetitiveness as Level,
    rule_clarity: values.rule_clarity as Level,
    criticality: values.criticality as Level,
    input_type: values.input_type as InputType,
    integration_readiness: values.integration_readiness as IntegrationReadiness,
    tools: values.tools
      .split(",")
      .map((tool) => tool.trim())
      .filter(Boolean),
    requires_human_judgement: values.requires_human_judgement,
    requires_human_approval: values.requires_human_approval,
    handles_sensitive_data: values.handles_sensitive_data,
  } satisfies StepUpdate;
}

/**
 * Adds a step to the process or, given `step`, edits it, as stepForm in
 * web/process-views.js. A field the API refuses shows its message and the form keeps every
 * value; a saved step calls onSaved.
 */
export function StepForm({
  processId,
  step,
  onSaved,
}: {
  processId: string;
  step?: Step;
  onSaved: () => void;
}) {
  const add = useAddStep(processId);
  const update = useUpdateStep();
  const toast = useToast();
  const [formError, setFormError] = useState<string[]>([]);
  const {
    register,
    handleSubmit,
    setError,
    formState: { errors },
  } = useForm<Values>({ defaultValues: toValues(step) });

  const handlers = {
    onSuccess: () => {
      toast(step ? "Step saved." : "Step added.");
      onSaved();
    },
    onError: (error: Error) => {
      if (error instanceof ApiError && error.isFieldError) {
        setFormError(applyFieldErrors(error, setError, FIELDS));
      }
    },
  };

  const submit = handleSubmit((values) => {
    setFormError([]);
    const body = toBody(values);
    if (step) update.mutate({ stepId: step.id, body }, handlers);
    // The API fills the descriptions this form does not ask for with their defaults.
    else add.mutate({ ...body, input_description: "", output_description: "" }, handlers);
  });

  const error = (name: FieldPath<Values>) => errors[name]?.message;
  const field = (name: FieldPath<Values>) => ({
    id: `step-${name}`,
    error: error(name),
    register: register(name),
  });

  return (
    <form onSubmit={submit} noValidate className="grid gap-4 sm:grid-cols-2">
      <TextField label="Name" required {...field("name")} />
      <TextField label="Responsible role" {...field("responsible_role")} />
      <TextField label="Description" multiline wide {...field("description")} />
      <NumberField label="Minutes per execution" required {...field("minutes_per_execution")} />
      <NumberField
        label="Occurrence rate (0 to 1)"
        hint="Share of executions that go through this step."
        {...field("occurrence_rate")}
      />
      <NumberField
        label="Exception rate (0 to 1)"
        hint="Leave empty if unknown."
        {...field("exception_rate")}
      />
      <SelectField
        label="Repetitiveness"
        options={LEVELS}
        current={step?.repetitiveness}
        {...field("repetitiveness")}
      />
      <SelectField
        label="Rule clarity"
        options={LEVELS}
        current={step?.rule_clarity}
        {...field("rule_clarity")}
      />
      <SelectField
        label="Criticality"
        options={LEVELS}
        current={step?.criticality}
        {...field("criticality")}
      />
      <SelectField
        label="Input type"
        options={INPUT_TYPES}
        current={step?.input_type}
        {...field("input_type")}
      />
      <SelectField
        label="Integration readiness"
        options={INTEGRATION_READINESS}
        current={step?.integration_readiness}
        {...field("integration_readiness")}
      />
      <TextField label="Tools" hint="Comma separated." {...field("tools")} />
      <fieldset className="flex flex-wrap gap-x-[22px] rounded-[10px] border border-line px-4 pt-1.5 pb-2 sm:col-span-2">
        <legend className="px-1.5 text-xs text-muted">Controls and data</legend>
        <CheckboxField label="Requires human judgement" {...field("requires_human_judgement")} />
        <CheckboxField label="Requires human approval" {...field("requires_human_approval")} />
        <CheckboxField label="Handles sensitive data" {...field("handles_sensitive_data")} />
      </fieldset>
      <Submit
        formError={formError}
        pending={add.isPending || update.isPending}
        label={step ? "Save step" : "Add step"}
        pendingLabel="Saving…"
      />
    </form>
  );
}
