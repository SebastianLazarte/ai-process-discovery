// The option lists of every enum a form offers, in the order web/ shows them: UNKNOWN first
// where the domain has it, because it is the honest default. Each list is typed with the
// enum of schema.d.ts and must name every member, so a new enum value fails typecheck here;
// options.test.ts also compares them with openapi.json.
import type { components } from "@/lib/api/schema";

type Schemas = components["schemas"];
export type Level = Schemas["Level"];
export type InputType = Schemas["InputType"];
export type IntegrationReadiness = Schemas["IntegrationReadiness"];
export type AutomationMethod = Schemas["AutomationMethod"];
export type HumanControl = Schemas["HumanControl"];
export type StepFrequency = Schemas["StepFrequency"];
export type ExceptionFrequency = Schemas["ExceptionFrequency"];

/** The list itself when it names every member of T, never otherwise. */
type Every<T, List extends readonly T[]> = [Exclude<T, List[number]>] extends [never]
  ? List
  : never;

function every<T>() {
  return <const List extends readonly T[]>(list: List & Every<T, List>): List => list;
}

export const LEVELS = every<Level>()(["UNKNOWN", "LOW", "MEDIUM", "HIGH"]);

export const INPUT_TYPES = every<InputType>()([
  "UNKNOWN",
  "DIGITAL_STRUCTURED",
  "DIGITAL_UNSTRUCTURED",
  "MIXED",
  "PHYSICAL",
]);

export const INTEGRATION_READINESS = every<IntegrationReadiness>()([
  "UNKNOWN",
  "NONE",
  "PARTIAL",
  "GOOD",
]);

export const AUTOMATION_METHODS = every<AutomationMethod>()([
  "RULE_BASED",
  "API_INTEGRATION",
  "AI_CANDIDATE",
  "HYBRID",
  "MANUAL",
  "NEEDS_REVIEW",
]);

export const HUMAN_CONTROLS = every<HumanControl>()(["NONE", "RECOMMENDED", "REQUIRED"]);

// RS-115: how often a step happens and goes off the normal path, in the words a person can
// answer. The API turns each choice into a rate; the words in brackets only say what the
// choice stands for, and the client never derives a figure from them (hard rule 7).
export const FREQUENCIES = every<StepFrequency>()([
  "ALWAYS",
  "MOST_OF_THE_TIME",
  "HALF_OF_THE_TIME",
  "SOMETIMES",
  "RARELY",
]);

export const FREQUENCY_LABELS: Readonly<Record<StepFrequency, string>> = {
  ALWAYS: "Always",
  MOST_OF_THE_TIME: "Most of the time (about 3 in 4)",
  HALF_OF_THE_TIME: "Half of the time",
  SOMETIMES: "Sometimes (about 1 in 4)",
  RARELY: "Rarely (about 1 in 10)",
};

// "Don't know" comes last here: the answers read as a scale, and it is still the default.
export const EXCEPTION_FREQUENCIES = every<ExceptionFrequency>()([
  "ALMOST_NEVER",
  "SOMETIMES",
  "OFTEN",
  "ALMOST_ALWAYS",
  "UNKNOWN",
]);

export const EXCEPTION_LABELS: Readonly<Record<ExceptionFrequency, string>> = {
  ALMOST_NEVER: "Almost never",
  SOMETIMES: "Sometimes (about 1 in 10)",
  OFTEN: "Often (about 1 in 3)",
  ALMOST_ALWAYS: "Almost always",
  UNKNOWN: "Don't know",
};
