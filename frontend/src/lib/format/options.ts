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
