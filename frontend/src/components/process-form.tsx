"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { useForm } from "react-hook-form";
import type { FieldErrors, FieldPath, UseFormRegister } from "react-hook-form";

import { ApiError, applyFieldErrors } from "@/lib/api";
import { useCreateProcess, useUpdateProcess } from "@/lib/api/queries";
import type { ProcessCreate, ProcessRead } from "@/lib/api/queries";

import { buttonClass } from "./button";
import { NumberField, TextField } from "./field";
import { useToast } from "./toast";

// Values travel as typed; the API validates and converts them (hard rule 7). An empty
// hourly cost is sent as null, meaning unknown, never as zero.
type Values = {
  name: string;
  owner: string;
  executions_per_month: string;
  hourly_cost: string;
  description: string;
};

const FIELDS: FieldPath<Values>[] = [
  "name",
  "owner",
  "executions_per_month",
  "hourly_cost",
  "description",
];

function toValues(process?: ProcessRead): Values {
  return {
    name: process?.name ?? "",
    owner: process?.owner ?? "",
    executions_per_month: String(process?.executions_per_month ?? 100),
    hourly_cost: process?.hourly_cost ?? "",
    description: process?.description ?? "",
  };
}

function toBody(values: Values): ProcessCreate {
  return {
    name: values.name.trim(),
    owner: values.owner.trim() || null,
    // The API parses numbers; the generated type says number, the wire carries text.
    executions_per_month: values.executions_per_month as unknown as number,
    hourly_cost: values.hourly_cost.trim() || null,
    description: values.description.trim(),
  };
}

/** The form of a new process, on the home page. */
export function ProcessForm() {
  const router = useRouter();
  const create = useCreateProcess();
  const [formError, setFormError] = useState<string[]>([]);
  const {
    register,
    handleSubmit,
    setError,
    formState: { errors },
  } = useForm<Values>({ defaultValues: toValues() });

  const submit = handleSubmit((values) => {
    setFormError([]);
    create.mutate(toBody(values), {
      onSuccess: (process) => router.push(`/processes/${process.id}`),
      onError: (error) => {
        if (error instanceof ApiError && error.isFieldError) {
          setFormError(applyFieldErrors(error, setError, FIELDS));
        }
      },
    });
  });

  return (
    <form onSubmit={submit} noValidate className="grid gap-4 sm:grid-cols-2">
      <ProcessFields register={register} errors={errors} />
      <Submit
        formError={formError}
        pending={create.isPending}
        label="Create process"
        pendingLabel="Creating…"
      />
    </form>
  );
}

/**
 * The settings of an existing process, on its Steps page, as processForm(process) in
 * web/process-views.js. Saving shows the values the API stored and, in the header, the new
 * process version.
 */
export function ProcessSettingsForm({ process }: { process: ProcessRead }) {
  const update = useUpdateProcess(process.id);
  const toast = useToast();
  const [formError, setFormError] = useState<string[]>([]);
  const {
    register,
    handleSubmit,
    setError,
    reset,
    formState: { errors },
  } = useForm<Values>({ defaultValues: toValues(process) });

  const submit = handleSubmit((values) => {
    setFormError([]);
    update.mutate(toBody(values), {
      onSuccess: (saved) => {
        reset(toValues(saved));
        toast("Process saved.");
      },
      onError: (error) => {
        if (error instanceof ApiError && error.isFieldError) {
          setFormError(applyFieldErrors(error, setError, FIELDS));
        }
      },
    });
  });

  return (
    <form onSubmit={submit} noValidate className="grid gap-4 sm:grid-cols-2">
      <ProcessFields register={register} errors={errors} idPrefix="process-" />
      <Submit
        formError={formError}
        pending={update.isPending}
        label="Save process"
        pendingLabel="Saving…"
      />
    </form>
  );
}

/** The five fields of a process. `idPrefix` keeps ids unique on a page with other forms. */
function ProcessFields({
  register,
  errors,
  idPrefix = "",
}: {
  register: UseFormRegister<Values>;
  errors: FieldErrors<Values>;
  idPrefix?: string;
}) {
  const error = (name: FieldPath<Values>) => errors[name]?.message;
  return (
    <>
      <TextField
        id={`${idPrefix}name`}
        label="Name"
        required
        error={error("name")}
        register={register("name")}
      />
      <TextField
        id={`${idPrefix}owner`}
        label="Owner"
        error={error("owner")}
        register={register("owner")}
      />
      <NumberField
        id={`${idPrefix}executions_per_month`}
        label="Executions per month"
        integer
        required
        error={error("executions_per_month")}
        register={register("executions_per_month")}
      />
      <NumberField
        id={`${idPrefix}hourly_cost`}
        label="Hourly cost"
        hint="Leave empty if unknown. Unknown is not free."
        error={error("hourly_cost")}
        register={register("hourly_cost")}
      />
      <TextField
        id={`${idPrefix}description`}
        label="Description"
        multiline
        wide
        error={error("description")}
        register={register("description")}
      />
    </>
  );
}

/** The messages no field claimed, then the submit button. */
export function Submit({
  formError,
  pending,
  label,
  pendingLabel,
}: {
  formError: string[];
  pending: boolean;
  label: string;
  pendingLabel: string;
}) {
  return (
    <>
      {formError.length > 0 && (
        <p role="alert" className="text-[13px] whitespace-pre-line text-bad sm:col-span-2">
          {formError.join(" ")}
        </p>
      )}
      <div className="sm:col-span-2">
        <button type="submit" className={buttonClass("primary")} disabled={pending}>
          {pending ? pendingLabel : label}
        </button>
      </div>
    </>
  );
}
