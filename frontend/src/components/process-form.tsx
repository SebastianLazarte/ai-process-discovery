"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { useForm } from "react-hook-form";
import type { FieldPath } from "react-hook-form";

import { ApiError, applyFieldErrors } from "@/lib/api";
import { useCreateProcess } from "@/lib/api/queries";

import { buttonClass } from "./button";
import { NumberField, TextField } from "./field";

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

  const error = (name: FieldPath<Values>) => errors[name]?.message;

  return (
    <form onSubmit={submit} noValidate className="grid gap-4 sm:grid-cols-2">
      <TextField
        id="name"
        label="Name"
        required
        error={error("name")}
        register={register("name")}
      />
      <TextField id="owner" label="Owner" error={error("owner")} register={register("owner")} />
      <NumberField
        id="executions_per_month"
        label="Executions per month"
        integer
        required
        error={error("executions_per_month")}
        register={register("executions_per_month")}
      />
      <NumberField
        id="hourly_cost"
        label="Hourly cost"
        hint="Leave empty if unknown. Unknown is not free."
        error={error("hourly_cost")}
        register={register("hourly_cost")}
      />
      <TextField
        id="description"
        label="Description"
        multiline
        wide
        error={error("description")}
        register={register("description")}
      />
      {formError.length > 0 && (
        <p role="alert" className="text-[13px] whitespace-pre-line text-bad sm:col-span-2">
          {formError.join(" ")}
        </p>
      )}
      <div className="sm:col-span-2">
        <button type="submit" className={buttonClass("primary")} disabled={create.isPending}>
          {create.isPending ? "Creating…" : "Create process"}
        </button>
      </div>
    </form>
  );
}
