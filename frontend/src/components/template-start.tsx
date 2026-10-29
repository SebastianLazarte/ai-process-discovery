"use client";

import { useRouter } from "next/navigation";
import { Fragment, useState } from "react";
import { useFieldArray, useForm } from "react-hook-form";
import type { FieldPath } from "react-hook-form";

import { ApiError, applyFieldErrors } from "@/lib/api";
import { useCreateProcess, useProcessTemplates } from "@/lib/api/queries";
import type { ProcessCreate, ProcessTemplate } from "@/lib/api/queries";
import { enumLabel } from "@/lib/format";

import { Badge } from "./badge";
import { ChoiceField, NumberField, TextField } from "./field";
import { Panel } from "./panel";
import { ProcessForm, Submit } from "./process-form";

// RS-96: start a process from a template of the catalog (RS-95, RS-97). The template brings
// the steps and their qualitative traits; the person types only the numbers of their
// company. "Other" in either list starts a blank process, as the home page does.

const OTHER = "other";
const OTHER_CHOICE = { value: OTHER, label: "Other" };

/** The sector and process lists, then the review of the chosen template or a blank form. */
export function TemplateStart() {
  const catalog = useProcessTemplates();
  const [sectorId, setSectorId] = useState("");
  const [slug, setSlug] = useState("");

  const sectors = catalog.data ?? [];
  const sector = sectors.find((candidate) => candidate.id === sectorId);
  const template = sector?.templates.find((candidate) => candidate.slug === slug);
  const blank = sectorId === OTHER || slug === OTHER;

  return (
    <div className="grid gap-6">
      <Panel id="start-point-title" title="Start point" className="max-w-3xl">
        <div className="grid gap-4 sm:grid-cols-2">
          <ChoiceField
            id="template-sector"
            label="Sector"
            placeholder="Choose a sector"
            choices={[...sectors.map(({ id, name }) => ({ value: id, label: name })), OTHER_CHOICE]}
            value={sectorId}
            onChange={(value) => {
              setSectorId(value);
              setSlug("");
            }}
          />
          {sector && (
            <ChoiceField
              id="template-process"
              label="Process"
              placeholder="Choose a process"
              choices={[
                ...sector.templates.map(({ slug, name }) => ({ value: slug, label: name })),
                OTHER_CHOICE,
              ]}
              value={slug}
              onChange={setSlug}
            />
          )}
        </div>
        <p className="mt-3 text-xs text-muted">
          Other starts a blank process that you describe yourself.
        </p>
      </Panel>
      {template && <TemplateReview key={`${sectorId}/${slug}`} template={template} />}
      {blank && (
        <Panel id="new-process-title" title="Process" className="max-w-3xl">
          <ProcessForm />
        </Panel>
      )}
    </div>
  );
}

// Values travel as typed; the API validates and converts them (hard rule 7). The client
// checks only that the figures a template cannot know are there: minutes for every step
// and executions per month. An empty hourly cost or exception rate is sent as null,
// meaning unknown, never as zero. Each step keeps the traits of its template, unedited.
type Traits = ProcessTemplate["steps"][number];
type StepFigures = {
  minutes_per_execution: string;
  occurrence_rate: string;
  exception_rate: string;
};
type StepValues = StepFigures & { traits: Traits };
type Values = {
  name: string;
  owner: string;
  executions_per_month: string;
  hourly_cost: string;
  description: string;
  steps: StepValues[];
};

const PROCESS_FIELDS: FieldPath<Values>[] = [
  "name",
  "owner",
  "executions_per_month",
  "hourly_cost",
  "description",
];

function toValues(template: ProcessTemplate): Values {
  return {
    name: template.name,
    owner: "",
    executions_per_month: "",
    hourly_cost: "",
    description: template.description,
    steps: template.steps.map((traits) => ({
      traits,
      minutes_per_execution: "",
      occurrence_rate: "1",
      exception_rate: "",
    })),
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
    steps: values.steps.map((step) => ({
      ...step.traits,
      minutes_per_execution: step.minutes_per_execution,
      occurrence_rate: step.occurrence_rate,
      exception_rate: step.exception_rate.trim() || null,
    })),
  };
}

const filled = (message: string) => (value: string) => value.trim() !== "" || message;

/** The chosen template, its steps with their traits, and the numbers only the person knows. */
function TemplateReview({ template }: { template: ProcessTemplate }) {
  const router = useRouter();
  const create = useCreateProcess();
  const [formError, setFormError] = useState<string[]>([]);
  const {
    control,
    register,
    handleSubmit,
    setError,
    formState: { errors },
  } = useForm<Values>({ defaultValues: toValues(template) });
  const { fields } = useFieldArray({ control, name: "steps" });

  // Step paths come first, so a step's "name" never lands on the process name.
  const names: FieldPath<Values>[] = [
    ...template.steps.flatMap((_, index) =>
      (["minutes_per_execution", "occurrence_rate", "exception_rate"] as const).map(
        (field) => `steps.${index}.${field}` as const,
      ),
    ),
    ...PROCESS_FIELDS,
  ];

  const submit = handleSubmit((values) => {
    setFormError([]);
    create.mutate(toBody(values), {
      onSuccess: (process) => router.push(`/processes/${process.id}`),
      onError: (error) => {
        if (error instanceof ApiError && error.isFieldError) {
          setFormError(applyFieldErrors(error, setError, names));
        }
      },
    });
  });

  return (
    <Panel id="template-review-title" title={`Review: ${template.name}`} className="max-w-3xl">
      <p className="mb-5 text-sm text-muted">
        The steps and their traits come from the template; you can change any of them on the Steps
        page once the process exists. Type the figures of your company: a template never carries
        one.
      </p>
      <form onSubmit={submit} noValidate className="grid gap-4 sm:grid-cols-2">
        <TextField
          id="template-name"
          label="Name"
          required
          error={errors.name?.message}
          register={register("name")}
        />
        <TextField
          id="template-owner"
          label="Owner"
          error={errors.owner?.message}
          register={register("owner")}
        />
        <NumberField
          id="template-executions_per_month"
          label="Executions per month"
          integer
          required
          error={errors.executions_per_month?.message}
          register={register("executions_per_month", {
            validate: filled("Enter the executions per month."),
          })}
        />
        <NumberField
          id="template-hourly_cost"
          label="Hourly cost"
          hint="Leave empty if unknown. Unknown is not free."
          error={errors.hourly_cost?.message}
          register={register("hourly_cost")}
        />
        <TextField
          id="template-description"
          label="Description"
          multiline
          wide
          error={errors.description?.message}
          register={register("description")}
        />
        <ol className="grid gap-4 sm:col-span-2">
          {fields.map((field, index) => {
            const { traits } = field;
            const stepErrors = errors.steps?.[index];
            const id = (name: keyof StepFigures) => `template-step-${index}-${name}`;
            return (
              <li key={field.id}>
                <fieldset className="grid gap-4 rounded-[10px] border border-line p-4 sm:grid-cols-3">
                  <legend className="px-1.5 text-sm font-semibold">
                    {index + 1}. {traits.name}
                  </legend>
                  <StepTraits traits={traits} />
                  <NumberField
                    id={id("minutes_per_execution")}
                    label="Minutes per execution"
                    required
                    error={stepErrors?.minutes_per_execution?.message}
                    register={register(`steps.${index}.minutes_per_execution`, {
                      validate: filled("Enter the minutes per execution."),
                    })}
                  />
                  <NumberField
                    id={id("occurrence_rate")}
                    label="Occurrence rate (0 to 1)"
                    hint="Share of executions that go through this step."
                    error={stepErrors?.occurrence_rate?.message}
                    register={register(`steps.${index}.occurrence_rate`)}
                  />
                  <NumberField
                    id={id("exception_rate")}
                    label="Exception rate (0 to 1)"
                    hint="Leave empty if unknown."
                    error={stepErrors?.exception_rate?.message}
                    register={register(`steps.${index}.exception_rate`)}
                  />
                </fieldset>
              </li>
            );
          })}
        </ol>
        <Submit
          formError={formError}
          pending={create.isPending}
          label="Create process"
          pendingLabel="Creating…"
        />
      </form>
    </Panel>
  );
}

const LEVEL_TRAITS = [
  ["Repetitiveness", "repetitiveness"],
  ["Rule clarity", "rule_clarity"],
  ["Input type", "input_type"],
  ["Integration readiness", "integration_readiness"],
  ["Criticality", "criticality"],
] as const;

const FLAGS = [
  ["Requires human judgement", "requires_human_judgement"],
  ["Requires human approval", "requires_human_approval"],
  ["Handles sensitive data", "handles_sensitive_data"],
] as const;

/** The traits a template fills in for a step, read only. */
function StepTraits({ traits }: { traits: Traits }) {
  const flags = FLAGS.filter(([, key]) => traits[key]).map(([label]) => label);
  return (
    <div className="grid gap-3 text-sm sm:col-span-3">
      {traits.description && <p className="text-ink-soft">{traits.description}</p>}
      <dl className="grid grid-cols-[max-content_1fr] gap-x-4 gap-y-1 text-[13px]">
        <dt className="text-muted">Responsible role</dt>
        <dd>{traits.responsible_role || "Not set"}</dd>
        <dt className="text-muted">Tools</dt>
        <dd>{traits.tools?.length ? traits.tools.join(", ") : "None"}</dd>
        {LEVEL_TRAITS.map(([label, key]) => (
          <Fragment key={key}>
            <dt className="text-muted">{label}</dt>
            <dd>{enumLabel(traits[key])}</dd>
          </Fragment>
        ))}
        {traits.problems && traits.problems.length > 0 && (
          <>
            <dt className="text-muted">Problems</dt>
            <dd>{traits.problems.join("; ")}</dd>
          </>
        )}
      </dl>
      {flags.length > 0 && (
        <ul aria-label="Controls and data" className="flex flex-wrap gap-2">
          {flags.map((label) => (
            <li key={label}>
              <Badge tone="warn">{label}</Badge>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
