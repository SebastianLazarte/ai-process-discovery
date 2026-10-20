// RS-94: the Blueprint tab renders the eight sections of the API's JSON as text, and the
// Markdown download is the API's own file, untouched by the client.
import { cleanup, screen, within } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { fakeApi } from "@/test/fake-api";
import { ANALYSIS_ID, STEP_ID, blueprint, processRead, step } from "@/test/fixtures";
import { renderWithProviders } from "@/test/render";

import { BlueprintView } from "./blueprint-view";

const INJECTED = '<img src="x" onerror="alert(1)">';
const PROCESS = processRead({ steps: [step()] });
const BLUEPRINT = blueprint({
  process_summary: {
    name: PROCESS.name,
    description: `Claims ${INJECTED}`,
    owner: "After-sales",
    executions_per_month: 180,
    steps: 1,
    process_version: 1,
    analysed_at: "2026-10-16T10:00:00+00:00",
    rules_version: "1.0.0",
    llm: "not_requested",
  },
  automation_opportunities: [
    {
      position: 1,
      name: `Read the claim email ${INJECTED}`,
      method: "HYBRID",
      human_control: "REQUIRED",
      decided_by: "HUMAN",
      monthly_hours: "12.00",
      suitability_score: 64,
      rationale: "Overridden by a person: the claims team checks every draft.",
    },
  ],
  proposed_architecture: ["Automated draft with a person confirming the result"],
  business_impact: {
    ...blueprint().business_impact,
    implementation_cost: "5000.00",
    assumptions: {
      implementation_cost: "5000.00",
      monthly_tooling_cost: "50.00",
      expected_time_reduction_by_step: { [STEP_ID]: "0.5" },
    },
  },
  risks: [{ source: "RULES", type: "sensitive_data", description: "Claims carry addresses." }],
  workflow_specification: ["Receive the claim email.", "Draft the claim record."],
});

const BLUEPRINT_PATH = `/analyses/${ANALYSIS_ID}/blueprint`;

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

function renderBlueprint() {
  const calls = fakeApi({
    [`GET ${BLUEPRINT_PATH}`]: { body: BLUEPRINT },
    [`GET /processes/${PROCESS.id}`]: { body: PROCESS },
  });
  renderWithProviders(<BlueprintView id={PROCESS.id} analysisId={ANALYSIS_ID} />);
  return calls;
}

describe("the Blueprint tab", () => {
  it("renders the eight sections as text built from the API's JSON, injecting no HTML", async () => {
    renderBlueprint();

    await screen.findByRole("heading", { level: 2, name: "1. Process summary" });
    expect(screen.getAllByRole("heading", { level: 2 }).map((h) => h.textContent)).toEqual([
      "1. Process summary",
      "2. Current state",
      "3. Automation opportunities",
      "4. Proposed architecture",
      "5. Business impact",
      "6. Risks",
      "7. Human controls",
      "8. Workflow specification",
    ]);

    // Markup in the data stays text: no element is built from it.
    expect(screen.getByText(`Claims ${INJECTED}`)).toBeDefined();
    const table = screen.getByRole("table", { name: "3. Automation opportunities" });
    const row = within(table).getAllByRole("row")[1]!;
    expect(within(row).getByText(`Read the claim email ${INJECTED}`)).toBeDefined();
    expect(screen.queryByRole("img")).toBeNull();

    // The override applied by a person, and the assumptions behind every figure.
    expect(within(row).getByText("Human")).toBeDefined();
    expect(within(row).getByText("Hybrid")).toBeDefined();
    const assumptions = screen.getByRole("list", { name: "Assumptions" });
    expect(
      within(assumptions)
        .getAllByRole("listitem")
        .map((li) => li.textContent),
    ).toEqual([
      "Implementation cost: 5,000.00",
      "Monthly tooling cost: 50.00",
      "Expected time reduction, Read the claim email: 50%",
    ]);
    expect(screen.getAllByRole("listitem").map((li) => li.textContent)).toContain(
      "Draft the claim record.",
    );
  });

  it("downloads the API's blueprint.md itself, so the file is identical to it", async () => {
    const calls = renderBlueprint();

    const link = await screen.findByRole("link", { name: "Download .md" });
    expect(link.getAttribute("href")).toBe(`/api/analyses/${ANALYSIS_ID}/blueprint.md`);
    expect(link.getAttribute("download")).toBe("blueprint-66666666.md");
    // The browser fetches the file; the client never reads or rebuilds the Markdown.
    expect(calls).not.toContain(`GET ${BLUEPRINT_PATH}.md`);
  });
});
