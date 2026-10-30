// RS-96: start a process from a sector template, review it and type only the numbers.
import { cleanup, fireEvent, screen, waitFor, within } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { fakeApi } from "@/test/fake-api";
import { processRead, sectorTemplates } from "@/test/fixtures";
import { push, renderWithProviders } from "@/test/render";

import { TemplateStart } from "./template-start";

vi.mock("next/navigation", async () => ({ useRouter: () => ({ push }) }));

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
  push.mockReset();
});

const CREATED_ID = "33333333-3333-4333-8333-333333333333";

function serve(extra: Parameters<typeof fakeApi>[0] = {}) {
  return fakeApi({ "GET /process-templates": { body: [sectorTemplates()] }, ...extra });
}

async function choose(sector: string, process?: string) {
  const sectors = screen.getByRole("combobox", { name: "Sector" });
  await within(sectors).findByRole("option", { name: "Manufacturing" });
  fireEvent.change(sectors, {
    target: { value: within(sectors).getByRole("option", { name: sector }).getAttribute("value") },
  });
  if (process === undefined) return;
  const processes = screen.getByRole("combobox", { name: "Process" });
  fireEvent.change(processes, {
    target: {
      value: within(processes).getByRole("option", { name: process }).getAttribute("value"),
    },
  });
}

function type(within_: HTMLElement, label: string, value: string) {
  fireEvent.change(within(within_).getByLabelText(label, { exact: false }), { target: { value } });
}

function valueOf(scope: HTMLElement, label: string) {
  return (within(scope).getByLabelText(label, { exact: false }) as HTMLInputElement).value;
}

function optionNames(name: string) {
  return within(screen.getByRole("combobox", { name }))
    .getAllByRole("option")
    .map((option) => option.textContent);
}

describe("RS-96.1: choosing a sector and one of its processes", () => {
  it("shows a review of its steps with their traits filled in", async () => {
    serve();
    renderWithProviders(<TemplateStart />);

    await choose("Manufacturing", "Supplier invoice processing");

    const review = screen.getByRole("region", { name: "Review: Supplier invoice processing" });
    expect(valueOf(review, "Name")).toBe("Supplier invoice processing");
    const first = within(review).getByRole("group", { name: "1. Receive the invoice" });
    for (const text of ["Accounts payable clerk", "Shared mailbox", "Mixed", "Partial"]) {
      expect(within(first).getByText(text)).toBeDefined();
    }
    expect(within(first).getByText("Invoices get lost in the mailbox")).toBeDefined();
    const second = within(review).getByRole("group", { name: "2. Approve the payment" });
    const controls = within(second).getByRole("list", { name: "Controls and data" });
    expect(
      within(controls)
        .getAllByRole("listitem")
        .map((item) => item.textContent),
    ).toEqual(["Requires human judgement", "Requires human approval", "Handles sensitive data"]);
    expect(valueOf(first, "Minutes per execution")).toBe("");
  });
});

describe("RS-96.2: creating without the figures a template cannot know", () => {
  it("marks the missing minutes and executions per month and sends nothing", async () => {
    const calls = serve();
    renderWithProviders(<TemplateStart />);
    await choose("Manufacturing", "Supplier invoice processing");
    const review = screen.getByRole("region", { name: "Review: Supplier invoice processing" });
    type(within(review).getByRole("group", { name: "1. Receive the invoice" }), "Minutes", "6");

    fireEvent.click(within(review).getByRole("button", { name: "Create process" }));

    const executions = within(review).getByLabelText("Executions per month", { exact: false });
    await waitFor(() => expect(executions.getAttribute("aria-invalid")).toBe("true"));
    expect(within(review).getByText("Enter the executions per month.")).toBeDefined();
    const second = within(review).getByRole("group", { name: "2. Approve the payment" });
    const missing = within(second).getByLabelText("Minutes per execution", { exact: false });
    expect(missing.getAttribute("aria-invalid")).toBe("true");
    expect(within(second).getByText("Enter the minutes per execution.")).toBeDefined();
    const filled = within(review).getByRole("group", { name: "1. Receive the invoice" });
    expect(
      within(filled)
        .getByLabelText("Minutes per execution", { exact: false })
        .getAttribute("aria-invalid"),
    ).toBeNull();
    expect(calls).toEqual(["GET /process-templates"]);
  });
});

describe("RS-96.3: creating a completed review", () => {
  it("saves the process with its steps in one request and opens its Steps page", async () => {
    let sent: unknown;
    const calls = serve({
      "POST /processes": async (request) => {
        sent = await request.json();
        return { status: 201, body: processRead({ id: CREATED_ID }) };
      },
    });
    renderWithProviders(<TemplateStart />);
    await choose("Manufacturing", "Supplier invoice processing");
    const review = screen.getByRole("region", { name: "Review: Supplier invoice processing" });
    const [first, second] = [
      within(review).getByRole("group", { name: "1. Receive the invoice" }),
      within(review).getByRole("group", { name: "2. Approve the payment" }),
    ];
    type(review, "Executions per month", "300");
    type(first, "Minutes", "6");
    type(first, "Exception rate", "0.1");
    type(second, "Minutes", "3");
    type(second, "Occurrence rate", "0.4");

    fireEvent.click(within(review).getByRole("button", { name: "Create process" }));

    await waitFor(() => expect(push).toHaveBeenCalledWith(`/processes/${CREATED_ID}`));
    expect(calls).toEqual(["GET /process-templates", "POST /processes"]);
    const [traitsOne, traitsTwo] = sectorTemplates().templates[0]!.steps;
    expect(sent).toEqual({
      name: "Supplier invoice processing",
      owner: null,
      executions_per_month: "300",
      hourly_cost: null,
      description: "Supplier invoices are received, matched and posted for payment.",
      steps: [
        { ...traitsOne, minutes_per_execution: "6", occurrence_rate: "1", exception_rate: "0.1" },
        { ...traitsTwo, minutes_per_execution: "3", occurrence_rate: "0.4", exception_rate: null },
      ],
    });
  });

  it("puts a field error of the API on its step", async () => {
    serve({
      "POST /processes": {
        status: 422,
        body: {
          detail: [{ loc: ["body", "steps", 1, "occurrence_rate"], msg: "Must be at most 1" }],
        },
      },
    });
    renderWithProviders(<TemplateStart />);
    await choose("Manufacturing", "Supplier invoice processing");
    const review = screen.getByRole("region", { name: "Review: Supplier invoice processing" });
    const second = within(review).getByRole("group", { name: "2. Approve the payment" });
    type(review, "Executions per month", "300");
    type(within(review).getByRole("group", { name: "1. Receive the invoice" }), "Minutes", "6");
    type(second, "Minutes", "3");
    type(second, "Occurrence rate", "4");

    fireEvent.click(within(review).getByRole("button", { name: "Create process" }));

    const rate = within(second).getByLabelText("Occurrence rate", { exact: false });
    await waitFor(() => expect(rate.getAttribute("aria-invalid")).toBe("true"));
    expect(within(second).getByText("Must be at most 1")).toBeDefined();
    expect(push).not.toHaveBeenCalled();
  });
});

describe("RS-96.4: the sector and process lists", () => {
  it("each end with Other", async () => {
    serve();
    renderWithProviders(<TemplateStart />);

    await choose("Manufacturing");

    expect(optionNames("Sector")).toEqual(["Choose a sector", "Manufacturing", "Other"]);
    expect(optionNames("Process")).toEqual([
      "Choose a process",
      "Supplier invoice processing",
      "Customer order entry",
      "Other",
    ]);
  });

  it("start a blank process from Other", async () => {
    serve();
    renderWithProviders(<TemplateStart />);

    await choose("Manufacturing", "Other");

    const blank = screen.getByRole("region", { name: "Process" });
    expect(valueOf(blank, "Name")).toBe("");
    expect(screen.queryByRole("region", { name: /^Review/ })).toBeNull();
  });
});
