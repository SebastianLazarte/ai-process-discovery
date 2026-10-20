// RS-76: override a recommendation with a required reason. Each test names the criterion it
// proves; the others pin the behaviour of web/ that the new client copies (ADR 0015).
import { cleanup, fireEvent, screen, waitFor, within } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { AUTOMATION_METHODS, HUMAN_CONTROLS } from "@/lib/format/options";
import { fakeApi } from "@/test/fake-api";
import {
  ANALYSIS_ID,
  PROCESS_ID,
  STEP_ID,
  analysisRead,
  processRead,
  stepAssessment,
} from "@/test/fixtures";
import type { AnalysisRead } from "@/test/fixtures";
import { renderWithProviders } from "@/test/render";

import { ResultsView } from "../results-view";

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

const POST = `POST /analyses/${ANALYSIS_ID}/overrides`;

const OVERRIDE = {
  id: "77777777-7777-4777-8777-777777777777",
  step_id: STEP_ID,
  original_method: "RULE_BASED",
  original_human_control: "NONE",
  new_method: "MANUAL",
  new_human_control: "REQUIRED",
  reason: "Legal wants a person on it",
  created_at: "2026-10-20T09:00:00Z",
} as const;

/** The analysis once the override of OVERRIDE is applied, as the API returns it. */
const overridden = () =>
  analysisRead({
    step_assessments: [
      stepAssessment({
        final_method: "MANUAL",
        final_human_control: "REQUIRED",
        final_source: "HUMAN",
        override: OVERRIDE,
      }),
    ],
  });

/** Renders Results, opens its one step and returns that step and its override form. */
async function openStep(analysis: AnalysisRead, routes: Parameters<typeof fakeApi>[0] = {}) {
  const calls = fakeApi({
    [`GET /analyses/${ANALYSIS_ID}`]: { body: analysis },
    [`GET /processes/${PROCESS_ID}`]: { body: processRead() },
    ...routes,
  });
  renderWithProviders(<ResultsView id={PROCESS_ID} analysisId={ANALYSIS_ID} />);
  const name = analysis.step_assessments[0]!.name;
  const steps = await screen.findByRole("region", { name: "Step by step" });
  const summary = within(steps).getByText(name).closest("summary")!;
  fireEvent.click(summary);
  const details = summary.parentElement as HTMLDetailsElement;
  return {
    calls,
    details,
    form: within(details).getByRole("region", { name: `Override ${name}` }),
  };
}

const reason = (form: HTMLElement) => within(form).getByRole("textbox", { name: /^Reason/ });

describe("Override a recommendation", () => {
  it("marks the reason and sends nothing when it is empty (criterion 1)", async () => {
    const { calls, form } = await openStep(analysisRead());

    fireEvent.click(within(form).getByRole("button", { name: "Save override" }));

    await waitFor(() => expect(reason(form).getAttribute("aria-invalid")).toBe("true"));
    expect(within(form).getByText("Give a reason of at least 3 characters.")).toBeDefined();
    expect(reason(form).getAttribute("aria-required")).toBe("true");

    // Blank space is no reason either.
    fireEvent.change(reason(form), { target: { value: "   " } });
    fireEvent.click(within(form).getByRole("button", { name: "Save override" }));
    await waitFor(() => expect(reason(form).getAttribute("aria-invalid")).toBe("true"));

    expect(calls).not.toContain(POST);
  });

  it("shows Override with the reason and keeps the original visible, de-emphasised (criterion 2)", async () => {
    const { details } = await openStep(overridden());

    const decision = within(details).getByLabelText("Decision");
    expect(within(decision).getByText("Override")).toBeDefined();
    expect(within(decision).getByText("Manual")).toBeDefined();
    expect(within(decision).getByText("Control: Required")).toBeDefined();

    const override = within(details).getByRole("region", { name: "Override" });
    expect(within(override).getByText(/Legal wants a person on it/)).toBeDefined();
    expect(within(override).getByText(/Original recommendation/)).toBeDefined();
    // The original sits in neutral badges, so it never reads as the decision in force.
    for (const text of ["Rule based", "Control: None"])
      expect(within(override).getByText(text).dataset.tone).toBe("neutral");
  });

  it("sends the step, method, control and trimmed reason, then reopens the step with the override", async () => {
    const sent: { body?: Record<string, unknown> } = {};
    const { details, form } = await openStep(analysisRead(), {
      [POST]: async (request: Request) => {
        sent.body = (await request.json()) as Record<string, unknown>;
        return { status: 201, body: overridden() };
      },
    });

    const select = (name: string, value: string) =>
      fireEvent.change(within(form).getByRole("combobox", { name }), { target: { value } });
    select("Method", "MANUAL");
    select("Human control", "REQUIRED");
    fireEvent.change(reason(form), { target: { value: "  Legal wants a person on it " } });
    fireEvent.click(within(form).getByRole("button", { name: "Save override" }));

    expect(
      await screen.findByText("Override saved. The original recommendation is kept."),
    ).toBeDefined();
    expect(sent.body).toEqual({
      step_id: STEP_ID,
      method: "MANUAL",
      human_control: "REQUIRED",
      reason: "Legal wants a person on it",
    });
    expect(details.open).toBe(true);
    expect(within(details).getByRole("region", { name: "Override" })).toBeDefined();
    expect((reason(form) as HTMLInputElement).value).toBe("");
  });

  it("puts the API's 422 on the reason field and shows no toast", async () => {
    const { form } = await openStep(analysisRead(), {
      [POST]: {
        status: 422,
        body: {
          detail: [{ loc: ["body", "reason"], msg: "String should have at most 2000 characters" }],
        },
      },
    });

    fireEvent.change(reason(form), { target: { value: "A long reason" } });
    fireEvent.click(within(form).getByRole("button", { name: "Save override" }));

    await waitFor(() => expect(reason(form).getAttribute("aria-invalid")).toBe("true"));
    expect(within(form).getByText("String should have at most 2000 characters")).toBeDefined();
    expect((reason(form) as HTMLInputElement).value).toBe("A long reason");
    expect(screen.getByRole("status").textContent).toBe("");
  });

  it("offers every method and human control, starting from the decision in force", async () => {
    const { form } = await openStep(
      analysisRead({
        step_assessments: [
          stepAssessment({ final_method: "HYBRID", final_human_control: "RECOMMENDED" }),
        ],
      }),
    );

    const values = (name: string) => {
      const select = within(form).getByRole("combobox", { name }) as HTMLSelectElement;
      return { current: select.value, options: [...select.options].map((o) => o.value) };
    };
    expect(values("Method")).toEqual({ current: "HYBRID", options: [...AUTOMATION_METHODS] });
    expect(values("Human control")).toEqual({
      current: "RECOMMENDED",
      options: [...HUMAN_CONTROLS],
    });
  });
});
