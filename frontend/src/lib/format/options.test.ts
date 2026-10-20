// @vitest-environment node
// RS-74, criterion 2: every option list offers exactly the members of its domain enum, as
// the API publishes them in openapi.json.
import { readFileSync } from "node:fs";
import { join } from "node:path";

import { describe, expect, it } from "vitest";

import {
  AUTOMATION_METHODS,
  HUMAN_CONTROLS,
  INPUT_TYPES,
  INTEGRATION_READINESS,
  LEVELS,
} from "./options";

const openapi = JSON.parse(
  readFileSync(join(import.meta.dirname, "..", "..", "..", "openapi.json"), "utf-8"),
) as { components: { schemas: Record<string, { enum?: string[] }> } };

describe("option lists", () => {
  it.each([
    ["Level", LEVELS],
    ["InputType", INPUT_TYPES],
    ["IntegrationReadiness", INTEGRATION_READINESS],
    ["AutomationMethod", AUTOMATION_METHODS],
    ["HumanControl", HUMAN_CONTROLS],
  ])("%s offers every member of the enum, once", (name, options) => {
    const members = openapi.components.schemas[name]?.enum;
    expect(members).toBeDefined();
    expect([...options].sort()).toEqual([...members!].sort());
  });

  it("put the honest default first where the domain has one", () => {
    expect(LEVELS[0]).toBe("UNKNOWN");
    expect(INPUT_TYPES[0]).toBe("UNKNOWN");
    expect(INTEGRATION_READINESS[0]).toBe("UNKNOWN");
  });
});
