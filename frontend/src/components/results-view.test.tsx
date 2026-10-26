// RS-92, criteria 1 to 4: Results in four panels with the language of trust. Criterion 5
// (a demo opens its first analysis) is in home-view.test.tsx.
import { cleanup, screen, within } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { fakeApi } from "@/test/fake-api";
import {
  ANALYSIS_ID,
  PROCESS_ID,
  analysisRead,
  processRead,
  stepAssessment,
} from "@/test/fixtures";
import type { AnalysisRead } from "@/test/fixtures";
import { renderWithProviders } from "@/test/render";

import { ResultsView } from "./results-view";

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

function show(analysis: AnalysisRead) {
  fakeApi({
    [`GET /analyses/${ANALYSIS_ID}`]: { body: analysis },
    [`GET /processes/${PROCESS_ID}`]: { body: processRead() },
  });
  renderWithProviders(<ResultsView id={PROCESS_ID} analysisId={ANALYSIS_ID} />);
}

const panel = (name: string) => screen.getByRole("region", { name });

const KNOWN_IMPACT: AnalysisRead["business_impact"] = {
  ...analysisRead().business_impact,
  estimated_hours_saved: "6.5",
  estimated_monthly_savings: "1250",
  net_monthly_savings: "1200.5",
  implementation_cost: "4800",
  payback_months: "4.0",
  roi_12_months: "1.5",
};

describe("RS-92: Results", () => {
  it("shows the current state and four separate panels, and no combined score", async () => {
    show(analysisRead());

    expect(await screen.findByRole("region", { name: "Current state" })).toBeDefined();
    for (const name of ["Automation suitability", "Business impact", "Risk", "Human controls"])
      expect(panel(name)).toBeDefined();

    // The process score shows once, in the suitability panel; nothing merges the panels.
    expect(within(panel("Automation suitability")).getByText("/ 100")).toBeDefined();
    expect(screen.getAllByText("/ 100")).toHaveLength(1);
    expect(screen.queryByText(/combined|overall|total score/i)).toBeNull();
  });

  it("prints every figure as the API returns it", async () => {
    show(
      analysisRead({
        current_state: { monthly_hours: "12.5", monthly_cost: "375" },
        business_impact: KNOWN_IMPACT,
      }),
    );

    const state = await screen.findByRole("region", { name: "Current state" });
    expect(within(state).getByText("12.50 h")).toBeDefined();
    expect(within(state).getByText("375.00")).toBeDefined();
    const impact = panel("Business impact");
    for (const text of ["6.50 h", "1,200.50", "4.0 mo", "1,250.00", "4,800.00", "150%"])
      expect(within(impact).getByText(text)).toBeDefined();
    expect(within(impact).getByText("Your assumption")).toBeDefined();
  });

  it("shows a null figure as unknown with its reason, never 0", async () => {
    show(
      analysisRead({
        automation_suitability: { process_score: null, policy_version: "1.0.0" },
      }),
    );

    const state = await screen.findByRole("region", { name: "Current state" });
    expect(within(state).getByText("unknown")).toBeDefined();
    expect(within(state).getByText("Hourly cost not set")).toBeDefined();

    const impact = panel("Business impact");
    expect(within(impact).getAllByText("unknown")).toHaveLength(5);
    expect(within(impact).getAllByText("Hourly cost not set")).toHaveLength(4);
    expect(within(impact).getByText("Implementation cost not given")).toBeDefined();
    expect(within(impact).queryByText(/^0(\.0+)?( h| mo|%)?$/)).toBeNull();

    const suitability = panel("Automation suitability");
    expect(within(suitability).getByText("unknown")).toBeDefined();
    expect(
      within(suitability).getByText("The process takes no time, so there is nothing to weigh"),
    ).toBeDefined();
  });

  it("says why payback and ROI are unknown when every input is known", async () => {
    show(
      analysisRead({
        business_impact: {
          ...KNOWN_IMPACT,
          net_monthly_savings: "-20",
          implementation_cost: "0",
          payback_months: null,
          roi_12_months: null,
        },
      }),
    );

    const impact = await screen.findByRole("region", { name: "Business impact" });
    expect(
      within(impact).getByText("Net savings are not positive, so it never pays back"),
    ).toBeDefined();
    expect(within(impact).getByText("The implementation cost is zero")).toBeDefined();
  });

  it("says who decided each step in a text badge, and never puts the AI badge on a number", async () => {
    show(
      analysisRead({
        step_assessments: [
          stepAssessment({ step_id: "a1", position: 1, name: "Read", final_source: "RULES" }),
          stepAssessment({
            step_id: "a2",
            position: 2,
            name: "Classify",
            final_source: "AI",
            final_human_control: "REQUIRED",
          }),
          stepAssessment({
            step_id: "a3",
            position: 3,
            name: "Approve",
            final_source: "HUMAN",
            final_method: "MANUAL",
            override: {
              id: "o1",
              step_id: "a3",
              original_method: "RULE_BASED",
              original_human_control: "NONE",
              new_method: "MANUAL",
              new_human_control: "RECOMMENDED",
              reason: "Legal wants a person on it",
              created_at: "2026-10-16T11:00:00Z",
            },
          }),
        ],
        risks: [{ source: "AI", type: "data_quality", description: "Emails vary a lot." }],
      }),
    );

    const steps = await screen.findByRole("region", { name: "Step by step" });
    const decisions = within(steps).getAllByLabelText("Decision");
    expect(within(decisions[0]!).getByText("Rules")).toBeDefined();
    expect(within(decisions[1]!).getByText("AI")).toBeDefined();
    expect(within(decisions[2]!).getByText("Override")).toBeDefined();
    const override = within(steps).getByRole("region", { name: "Override" });
    expect(within(override).getByText(/Legal wants a person on it/)).toBeDefined();

    // Every AI badge sits with words, never beside a figure.
    for (const badge of screen.getAllByText("AI", { exact: true }))
      expect(badge.parentElement?.textContent).not.toMatch(/\d/);
  });

  it("shows the rules version, the prompt version and the LLM status", async () => {
    show(
      analysisRead({
        rules_version: "2.1.0",
        llm: {
          status: "ok",
          provider: "anthropic",
          model: "claude-sonnet-5-5",
          prompt_version: "step-v3",
          error_kind: null,
        },
      }),
    );

    const bar = await screen.findByRole("region", { name: "Provenance" });
    expect(bar.textContent).toContain("rules 2.1.0");
    expect(bar.textContent).toContain("prompt step-v3");
    expect(within(bar).getByText("LLM ok · anthropic/claude-sonnet-5-5")).toBeDefined();
  });

  it("says when the LLM was not requested and no prompt was used", async () => {
    show(analysisRead());

    const bar = await screen.findByRole("region", { name: "Provenance" });
    expect(within(bar).getByText("LLM not requested")).toBeDefined();
    expect(bar.textContent).toContain("prompt none");
  });

  it("says when the analysis does not exist", async () => {
    fakeApi({
      [`GET /analyses/${ANALYSIS_ID}`]: { status: 404, body: { detail: "analysis not found" } },
      [`GET /processes/${PROCESS_ID}`]: { body: processRead() },
    });
    renderWithProviders(<ResultsView id={PROCESS_ID} analysisId={ANALYSIS_ID} />);

    expect(await screen.findByText("This analysis does not exist.")).toBeDefined();
  });
});

// RS-75, criterion 4: the deterministic part never depends on the LLM.
describe("Results without the LLM", () => {
  const unavailable = (error_kind: string) =>
    analysisRead({
      llm: { status: "unavailable", provider: null, model: null, prompt_version: null, error_kind },
    });

  it("says the deterministic results are complete and today's AI quota is used up", async () => {
    show(unavailable("daily_quota"));

    const note = await screen.findByRole("note");
    expect(note.textContent).toMatch(/Today's AI quota of this demo is used up/);
    expect(note.textContent).toMatch(/The deterministic results are complete/);
  });

  it("names any other reason the LLM was unavailable", async () => {
    show(unavailable("timeout"));

    expect((await screen.findByRole("note")).textContent).toBe(
      "The LLM was unavailable (Timeout). The deterministic results are complete.",
    );
  });

  it("shows no note when the LLM was not requested", async () => {
    show(analysisRead());

    await screen.findByRole("region", { name: "Provenance" });
    expect(screen.queryByRole("note")).toBeNull();
  });
});
