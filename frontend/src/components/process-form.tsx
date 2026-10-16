"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { useForm } from "react-hook-form";
import type { FieldPath, UseFormRegisterReturn } from "react-hook-form";

import { ApiError, applyFieldErrors } from "@/lib/api";
import { useCreateProcess } from "@/lib/api/queries";

import { buttonClass } from "./button";

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

export function ProcessForm() {
  const router = useRouter();
  const create = useCreateProcess();
  const [formError, setFormError] = useState<string[]>([]);
  const {
    register,
    handleSubmit,
    setError,
    formState: { errors },
  } = useForm<Values>({
    defaultValues: {
      name: "",
      owner: "",
      executions_per_month: "100",
      hourly_cost: "",
      description: "",
    },
  });

  const submit = handleSubmit((values) => {
    setFormError([]);
    create.mutate(
      {
        name: values.name.trim(),
        owner: values.owner.trim() || null,
        // The API parses numbers; the generated type says number, the wire carries text.
        executions_per_month: values.executions_per_month as unknown as number,
        hourly_cost: values.hourly_cost.trim() || null,
        description: values.description.trim(),
      },
      {
        onSuccess: (process) => router.push(`/processes/${process.id}`),
        onError: (error) => {
          if (error instanceof ApiError && error.isFieldError) {
            setFormError(applyFieldErrors(error, setError, FIELDS));
          }
        },
      },
    );
  });

  const field = (name: FieldPath<Values>, label: string, hint?: string) => {
    const error = errors[name]?.message;
    const describedBy = [hint && `${name}-hint`, error && `${name}-error`]
      .filter(Boolean)
      .join(" ");
    return { error, describedBy: describedBy || undefined, label, hint };
  };

  return (
    <form onSubmit={submit} noValidate className="grid max-w-xl gap-5">
      <TextField {...field("name", "Name")} id="name" required register={register("name")} />
      <TextField {...field("owner", "Owner")} id="owner" register={register("owner")} />
      <TextField
        {...field("executions_per_month", "Executions per month")}
        id="executions_per_month"
        inputMode="numeric"
        required
        register={register("executions_per_month")}
      />
      <TextField
        {...field("hourly_cost", "Hourly cost", "Leave empty if unknown. Unknown is not free.")}
        id="hourly_cost"
        inputMode="decimal"
        register={register("hourly_cost")}
      />
      <TextField
        {...field("description", "Description")}
        id="description"
        multiline
        register={register("description")}
      />
      {formError.length > 0 && (
        <p role="alert" className="text-sm text-red-800">
          {formError.join(" ")}
        </p>
      )}
      <div>
        <button type="submit" className={buttonClass("primary")} disabled={create.isPending}>
          {create.isPending ? "Creating…" : "Create process"}
        </button>
      </div>
    </form>
  );
}

type TextFieldProps = {
  id: string;
  label: string;
  hint?: string;
  error?: string;
  describedBy?: string;
  required?: boolean;
  multiline?: boolean;
  inputMode?: "numeric" | "decimal";
  register: UseFormRegisterReturn;
};

function TextField({
  id,
  label,
  hint,
  error,
  describedBy,
  required,
  multiline,
  inputMode,
  register,
}: TextFieldProps) {
  const control = {
    id,
    "aria-invalid": error ? true : undefined,
    "aria-describedby": describedBy,
    "aria-required": required || undefined,
    className:
      "mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 aria-invalid:border-red-700",
    ...register,
  };
  return (
    <div>
      <label htmlFor={id} className="font-medium">
        {label}
        {required && <span className="text-gray-600"> (required)</span>}
      </label>
      {multiline ? (
        <textarea rows={3} {...control} />
      ) : (
        <input inputMode={inputMode} {...control} />
      )}
      {hint && (
        <p id={`${id}-hint`} className="mt-1 text-sm text-gray-600">
          {hint}
        </p>
      )}
      {error && (
        <p id={`${id}-error`} className="mt-1 text-sm text-red-800">
          {error}
        </p>
      )}
    </div>
  );
}
