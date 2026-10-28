// RS-74: add or edit a step. Each test names the criterion it proves.
import { cleanup, fireEvent, screen, waitFor, within } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { INPUT_TYPES, INTEGRATION_READINESS, LEVELS } from "@/lib/format/options";
import { fakeApi } from "@/test/fake-api";
import { STEP_ID, processRead, step } from "@/test/fixtures";
import type { StepRead } from "@/test/fixtures";
import { push, renderWithProviders } from "@/test/render";

import { StepsView } from "./steps-view";

vi.mock("next/navigation", async () => ({ useRouter: () => ({ push }) }));

const PATH = `/processes/${processRead().id}`;

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
  push.mockReset();
});

/** Renders the Steps page of a process with one step, and opens that step in the form. */
async function editStep(stored: StepRead, routes: Parameters<typeof fakeApi>[0] = {}) {
  const process = processRead({ steps: [stored] });
  const calls = fakeApi({ [`GET ${PATH}`]: { body: process }, ...routes });
  renderWithProviders(<StepsView id={process.id} />);
  fireEvent.click(await screen.findByRole("button", { name: `Edit ${stored.name}` }));
  return { calls, form: screen.getByRole("dialog", { name: `Edit step ${stored.position}` }) };
}

/** Answers PATCH /steps/{id} with the process and keeps the body it was sent. */
function savingStep() {
  const sent: { body?: Record<string, unknown> } = {};
  const route = {
    [`PATCH /steps/${STEP_ID}`]: async (request: Request) => {
      sent.body = (await request.json()) as Record<string, unknown>;
      return { body: processRead({ version: 2, steps: [step()] }) };
    },
  };
  return { sent, route };
}

const optionValues = (select: HTMLElement) =>
  within(select)
    .getAllByRole("option")
    .map((option) => (option as HTMLOptionElement).value);

describe("RS-74: the step form", () => {
  it("offers every member of each domain enum (criterion 2)", async () => {
    const { form } = await editStep(step());

    for (const [label, options] of [
      ["Repetitiveness", LEVELS],
      ["Rule clarity", LEVELS],
      ["Criticality", LEVELS],
      ["Input type", INPUT_TYPES],
      ["Integration readiness", INTEGRATION_READINESS],
    ] as const) {
      expect(optionValues(within(form).getByRole("combobox", { name: label }))).toEqual([
        ...options,
      ]);
    }
  });

  it("keeps a stored value the client does not list, and saving sends it back (criterion 3)", async () => {
    const { sent, route } = savingStep();
    const { form } = await editStep(step({ repetitiveness: "VERY_HIGH" as never }), route);

    const select = within(form).getByRole("combobox", { name: "Repetitiveness" });
    expect((select as HTMLSelectElement).value).toBe("VERY_HIGH");
    expect(within(select).getByRole("option", { name: "Very high" })).toBeDefined();

    fireEvent.click(within(form).getByRole("button", { name: "Save step" }));
    await waitFor(() => expect(sent.body).toBeDefined());
    expect(sent.body?.repetitiveness).toBe("VERY_HIGH");
  });

  it("reads an unknown exception rate as unknown and saves it untouched as null (criterion 4)", async () => {
    const { sent, route } = savingStep();
    const { form } = await editStep(step({ exception_rate: null }), route);

    expect(screen.getByText(/exception rate unknown/)).toBeDefined();
    const field = within(form).getByRole("textbox", { name: "Exception rate (0 to 1)" });
    expect((field as HTMLInputElement).value).toBe("");
    expect(document.getElementById(field.getAttribute("aria-describedby") ?? "")?.textContent).toBe(
      "Leave empty if unknown.",
    );

    fireEvent.click(within(form).getByRole("button", { name: "Save step" }));
    await waitFor(() => expect(sent.body).toBeDefined());
    expect(sent.body?.exception_rate).toBeNull();
    expect(await screen.findByText("Step saved.")).toBeDefined();
    expect(screen.queryByRole("dialog")).toBeNull();
  });

  it("shows the API's error on an occurrence rate outside 0 to 1 and keeps every value (criterion 5)", async () => {
    const { form } = await editStep(step(), {
      [`PATCH /steps/${STEP_ID}`]: {
        status: 422,
        body: {
          detail: [{ loc: ["body", "occurrence_rate"], msg: "Must be between 0 and 1" }],
        },
      },
    });

    const change = (name: string, value: string) =>
      fireEvent.change(within(form).getByRole("textbox", { name: new RegExp(`^${name}`) }), {
        target: { value },
      });
    change("Name", "Read and sort the claim email");
    change("Occurrence rate", "1.5");
    change("Tools", "Outlook, Excel");
    fireEvent.click(within(form).getByRole("button", { name: "Save step" }));

    const rate = within(form).getByRole("textbox", { name: "Occurrence rate (0 to 1)" });
    await waitFor(() => expect(rate.getAttribute("aria-invalid")).toBe("true"));
    expect(within(form).getByText("Must be between 0 and 1")).toBeDefined();
    expect((rate as HTMLInputElement).value).toBe("1.5");
    const value = (name: RegExp) =>
      (within(form).getByRole("textbox", { name }) as HTMLInputElement).value;
    expect(value(/^Name/)).toBe("Read and sort the claim email");
    expect(value(/^Tools/)).toBe("Outlook, Excel");
    expect(value(/^Responsible role/)).toBe("Claims clerk");
    expect(screen.getByRole("status").textContent).toBe("");
  });

  it("adds a step with the honest defaults: unknown levels and an unknown exception rate", async () => {
    let sent: Record<string, unknown> | undefined;
    const process = processRead();
    fakeApi({
      [`GET ${PATH}`]: { body: process },
      [`POST ${PATH}/steps`]: async (request) => {
        sent = (await request.json()) as Record<string, unknown>;
        return { status: 201, body: processRead({ version: 2, steps: [step()] }) };
      },
    });
    renderWithProviders(<StepsView id={process.id} />);

    fireEvent.click(await screen.findByRole("button", { name: "Add step" }));
    const form = screen.getByRole("dialog", { name: "Add a step" });
    fireEvent.change(within(form).getByRole("textbox", { name: /^Name/ }), {
      target: { value: "Check the warranty" },
    });
    fireEvent.click(within(form).getByRole("button", { name: "Add step" }));

    await waitFor(() => expect(sent).toBeDefined());
    expect(sent).toMatchObject({
      name: "Check the warranty",
      minutes_per_execution: "5",
      occurrence_rate: "1",
      exception_rate: null,
      repetitiveness: "UNKNOWN",
      input_type: "UNKNOWN",
      integration_readiness: "UNKNOWN",
      tools: [],
      handles_sensitive_data: false,
    });
    expect(await screen.findByRole("heading", { name: "Read the claim email" })).toBeDefined();
    expect(screen.getByRole("status").textContent).toBe("Step added.");
  });
});
