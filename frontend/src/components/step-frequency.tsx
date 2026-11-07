import type { UseFormRegisterReturn } from "react-hook-form";

import type { ProcessRead } from "@/lib/api/queries";
import { percent } from "@/lib/format";
import {
  EXCEPTION_FREQUENCIES,
  EXCEPTION_LABELS,
  FREQUENCIES,
  FREQUENCY_LABELS,
} from "@/lib/format/options";
import type { ExceptionFrequency, StepFrequency } from "@/lib/format/options";

import { SelectField } from "./field";

// RS-115: how often a step happens and goes off the normal path, asked in plain words. The
// form sends the choice; the API turns it into the rate the analysis uses. A step saved
// with an exact rate (the demos, the API) keeps it as the option "Exact figure", and while
// that option stays chosen the form sends nothing for it, so the rate is never rounded.

type Step = ProcessRead["steps"][number];

/** The choice that stands for an exact rate stored without a plain-word answer. */
export const EXACT = "EXACT";

export type FrequencyValues = { frequency: string; exception_frequency: string };

export function frequencyValues(step?: Step): FrequencyValues {
  if (!step) return { frequency: "ALWAYS", exception_frequency: "UNKNOWN" };
  return {
    frequency: step.frequency ?? EXACT,
    exception_frequency: step.exception_frequency ?? EXACT,
  };
}

/** The choices to send: an exact figure left as it is sends nothing. */
export function frequencyBody(values: FrequencyValues) {
  return {
    ...(values.frequency !== EXACT && { frequency: values.frequency as StepFrequency }),
    ...(values.exception_frequency !== EXACT && {
      exception_frequency: values.exception_frequency as ExceptionFrequency,
    }),
  };
}

/** How often the step runs and goes off the path, as the Steps list reads it. */
export function frequencyText(step: Step): string {
  const runs = step.frequency
    ? FREQUENCY_LABELS[step.frequency].toLowerCase()
    : `in ${percent(step.occurrence_rate)} of executions`;
  const exceptions = step.exception_frequency
    ? `exceptions: ${EXCEPTION_LABELS[step.exception_frequency].toLowerCase()}`
    : `exception rate ${percent(step.exception_rate)}`;
  return `runs ${runs} · ${exceptions}`;
}

function withExact<T extends string>(
  options: readonly T[],
  labels: Readonly<Record<T, string>>,
  exact: string | null | undefined,
): { options: readonly string[]; labels: Readonly<Partial<Record<string, string>>> } {
  if (exact === undefined) return { options, labels };
  return {
    options: [...options, EXACT],
    labels: { ...labels, [EXACT]: `Exact figure: ${percent(exact)}` },
  };
}

/** The two questions, for the step form and the template review. */
export function FrequencyFields({
  idPrefix,
  step,
  frequency,
  exceptions,
}: {
  idPrefix: string;
  step?: Step;
  frequency: { register: UseFormRegisterReturn; error?: string };
  exceptions: { register: UseFormRegisterReturn; error?: string };
}) {
  const runs = withExact(
    FREQUENCIES,
    FREQUENCY_LABELS,
    step && !step.frequency ? step.occurrence_rate : undefined,
  );
  const off = withExact(
    EXCEPTION_FREQUENCIES,
    EXCEPTION_LABELS,
    step && !step.exception_frequency ? step.exception_rate : undefined,
  );
  return (
    <>
      <SelectField
        id={`${idPrefix}-frequency`}
        label="How often does this step happen?"
        hint="Out of every execution of the process."
        {...runs}
        {...frequency}
      />
      <SelectField
        id={`${idPrefix}-exception_frequency`}
        label="How often does it go off the normal path?"
        hint="Cases that need special handling."
        {...off}
        {...exceptions}
      />
    </>
  );
}
