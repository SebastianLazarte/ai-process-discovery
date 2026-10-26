// RS-73: the Steps tab shows the facts of the process, an unknown hourly cost as unknown,
// and deletes the process after a confirmation that names it. RS-74: it lists the steps in
// order and saves the process settings. RS-91: it moves a step up or down and deletes one,
// and the list and the version follow the API.
import { cleanup, fireEvent, screen, waitFor, within } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { fakeApi } from "@/test/fake-api";
import { processRead, step } from "@/test/fixtures";
import { push, renderWithProviders } from "@/test/render";

import { ProcessView } from "./process-view";
import { StepsView } from "./steps-view";

vi.mock("next/navigation", async () => ({
  useRouter: () => ({ push }),
  usePathname: () => "/",
}));

const PROCESS = processRead();
const PATH = `/processes/${PROCESS.id}`;

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
  push.mockReset();
});

describe("the Steps tab", () => {
  it("shows an unknown hourly cost as unknown", async () => {
    fakeApi({ [`GET ${PATH}`]: { body: PROCESS } });
    renderWithProviders(<StepsView id={PROCESS.id} />);

    expect(
      (await screen.findByText("Hourly cost", { selector: "dt" })).nextElementSibling?.textContent,
    ).toBe("unknown");
    expect(screen.getByText("Costs stay unknown")).toBeDefined();
  });

  it("deletes the process only after a second, explicit confirmation", async () => {
    const calls = fakeApi({
      [`GET ${PATH}`]: { body: PROCESS },
      [`DELETE ${PATH}`]: { status: 204 },
      "GET /processes": { body: [] },
    });
    renderWithProviders(<StepsView id={PROCESS.id} />);

    fireEvent.click(await screen.findByRole("button", { name: "Delete process" }));
    expect(calls).not.toContain(`DELETE ${PATH}`);
    expect(
      screen.getByRole("group", { name: /and all its analyses\? This cannot be undone\./ }),
    ).toBeDefined();

    fireEvent.click(screen.getByRole("button", { name: "Delete for good" }));
    await waitFor(() => expect(push).toHaveBeenCalledWith("/"));
    expect(calls).toContain(`DELETE ${PATH}`);
    expect(screen.getByRole("status").textContent).toBe(`Deleted “${PROCESS.name}”.`);
  });

  it("keeps the process when the confirmation is withdrawn", async () => {
    const calls = fakeApi({ [`GET ${PATH}`]: { body: PROCESS } });
    renderWithProviders(<StepsView id={PROCESS.id} />);

    fireEvent.click(await screen.findByRole("button", { name: "Delete process" }));
    fireEvent.click(screen.getByRole("button", { name: "Keep it" }));

    expect(screen.getByRole("button", { name: "Delete process" })).toBeDefined();
    expect(calls).not.toContain(`DELETE ${PATH}`);
  });
});

describe("the step list", () => {
  it("RS-74.1: shows each step's position, name, minutes and occurrence rate, in order", async () => {
    const steps = [
      step(),
      step({
        id: "88888888-8888-4888-8888-888888888888",
        position: 2,
        name: "Check the warranty",
        responsible_role: "",
        minutes_per_execution: "12.5",
        occurrence_rate: "0.25",
        exception_rate: "0.1",
        requires_human_approval: true,
      }),
    ];
    fakeApi({ [`GET ${PATH}`]: { body: processRead({ steps }) } });
    renderWithProviders(<StepsView id={PROCESS.id} />);

    const list = await screen.findByRole("list", { name: "Steps" });
    const [first, second] = within(list).getAllByRole("listitem");
    expect(within(first!).getByText("01")).toBeDefined();
    expect(within(first!).getByRole("heading", { name: "Read the claim email" })).toBeDefined();
    expect(
      within(first!).getByText(/Claims clerk · 4\.0 min · runs in 100% of executions/),
    ).toBeDefined();
    expect(within(second!).getByText("02")).toBeDefined();
    expect(within(second!).getByRole("heading", { name: "Check the warranty" })).toBeDefined();
    expect(
      within(second!).getByText(
        "No role · 12.5 min · runs in 25% of executions · exception rate 10%",
      ),
    ).toBeDefined();
    expect(within(second!).getByText("Approval")).toBeDefined();
  });

  it("invites the first step when there is none", async () => {
    fakeApi({ [`GET ${PATH}`]: { body: PROCESS } });
    renderWithProviders(<StepsView id={PROCESS.id} />);

    expect(await screen.findByRole("heading", { name: "No steps yet" })).toBeDefined();
    expect(screen.queryByText(/step editor arrives/)).toBeNull();
  });
});

describe("the process settings", () => {
  it("save, then show the saved values and the new version; an empty hourly cost saves as unknown (RS-74, criterion 6)", async () => {
    let sent: unknown;
    const before = processRead({ hourly_cost: "45.00" });
    const saved = processRead({
      name: "Warranty claims",
      owner: "Service desk",
      executions_per_month: 220,
      hourly_cost: null,
      description: "Claims by email and phone.",
      version: 2,
    });
    fakeApi({
      [`GET ${PATH}`]: { body: before },
      [`GET ${PATH}/analyses`]: { body: [] },
      [`PATCH ${PATH}`]: async (request) => {
        sent = await request.json();
        return { body: saved };
      },
      "GET /processes": { body: [] },
    });
    renderWithProviders(
      <ProcessView id={PROCESS.id}>
        <StepsView id={PROCESS.id} />
      </ProcessView>,
    );

    const settings = await screen.findByRole("region", { name: "Process settings" });
    const field = (name: RegExp) =>
      within(settings).getByRole("textbox", { name }) as HTMLInputElement;
    expect(field(/^Hourly cost/).value).toBe("45.00");
    fireEvent.change(field(/^Name/), { target: { value: "Warranty claims" } });
    fireEvent.change(field(/^Owner/), { target: { value: "Service desk" } });
    fireEvent.change(field(/^Executions per month/), { target: { value: "220" } });
    fireEvent.change(field(/^Hourly cost/), { target: { value: "" } });
    fireEvent.change(field(/^Description/), { target: { value: "Claims by email and phone." } });
    fireEvent.click(within(settings).getByRole("button", { name: "Save process" }));

    expect(await screen.findByText("Process · v2")).toBeDefined();
    expect(sent).toEqual({
      name: "Warranty claims",
      owner: "Service desk",
      executions_per_month: "220",
      hourly_cost: null,
      description: "Claims by email and phone.",
    });
    expect(screen.getByRole("heading", { level: 1, name: "Warranty claims" })).toBeDefined();
    expect(field(/^Executions per month/).value).toBe("220");
    expect(field(/^Hourly cost/).value).toBe("");
    expect(screen.getByText("Costs stay unknown")).toBeDefined();
    expect(screen.getByRole("status").textContent).toBe("Process saved.");
  });
});

const THREE = ["Read the claim email", "Check the warranty", "Approve the refund"].map(
  (name, index) =>
    step({ id: `5555555${index}-5555-4555-8555-555555555555`, position: index + 1, name }),
);
const [STEP_A, STEP_B, STEP_C] = THREE as [ReturnType<typeof step>, ...ReturnType<typeof step>[]];

/** The process as the API stores it after a write: positions follow the order, version + 1. */
function stored(steps: ReturnType<typeof step>[], version = 2) {
  return processRead({
    version,
    steps: steps.map((each, index) => ({ ...each, position: index + 1 })),
  });
}

const stepRows = () => within(screen.getByRole("list", { name: "Steps" })).getAllByRole("listitem");

const stepNames = () =>
  within(screen.getByRole("list", { name: "Steps" }))
    .getAllByRole("heading", { level: 3 })
    .map((heading) => heading.textContent);

function renderProcess() {
  return renderWithProviders(
    <ProcessView id={PROCESS.id}>
      <StepsView id={PROCESS.id} />
    </ProcessView>,
  );
}

const frame = {
  [`GET ${PATH}/analyses`]: { body: [] },
  "GET /processes": { body: [] },
};

describe("RS-91: reordering steps", () => {
  it("moves the third step up from the keyboard, saves the order and keeps focus on it (criterion 1)", async () => {
    let sent: unknown;
    fakeApi({
      ...frame,
      [`GET ${PATH}`]: { body: processRead({ steps: THREE }) },
      [`PUT ${PATH}/steps/order`]: async (request) => {
        sent = await request.json();
        return { body: stored([STEP_A, STEP_C!, STEP_B!]) };
      },
    });
    renderProcess();

    const up = await screen.findByRole("button", { name: "Move Approve the refund up" });
    // A native, enabled button in the tab order: Tab reaches it and Enter or Space presses
    // it. jsdom does not turn a key press into the click a browser fires, so the test
    // focuses the button and dispatches that click.
    expect(up.tagName).toBe("BUTTON");
    expect(up.tabIndex).toBe(0);
    expect((up as HTMLButtonElement).disabled).toBe(false);
    up.focus();
    fireEvent.click(up);

    expect(await screen.findByText("Process · v2")).toBeDefined();
    expect(stepNames()).toEqual([
      "Read the claim email",
      "Approve the refund",
      "Check the warranty",
    ]);
    expect(sent).toEqual({ step_ids: [STEP_A.id, STEP_C!.id, STEP_B!.id] });
    expect(document.activeElement).toBe(
      screen.getByRole("button", { name: "Move Approve the refund up" }),
    );
    const moved = stepRows()[1]!;
    expect(within(moved).getByText("02")).toBeDefined();
  });

  it("keeps focus on a step that reaches the top, on the button that still works", async () => {
    fakeApi({
      ...frame,
      [`GET ${PATH}`]: { body: processRead({ steps: THREE }) },
      [`PUT ${PATH}/steps/order`]: { body: stored([STEP_B!, STEP_A, STEP_C!]) },
    });
    renderProcess();

    const up = await screen.findByRole("button", { name: "Move Check the warranty up" });
    up.focus();
    fireEvent.click(up);

    await screen.findByText("Process · v2");
    expect(stepNames()[0]).toBe("Check the warranty");
    expect(
      (screen.getByRole("button", { name: "Move Check the warranty up" }) as HTMLButtonElement)
        .disabled,
    ).toBe(true);
    expect(document.activeElement).toBe(
      screen.getByRole("button", { name: "Move Check the warranty down" }),
    );
  });

  it("cannot move the first step up or the last one down", async () => {
    fakeApi({ ...frame, [`GET ${PATH}`]: { body: processRead({ steps: THREE }) } });
    renderProcess();

    const button = async (name: string) =>
      (await screen.findByRole("button", { name })) as HTMLButtonElement;
    expect((await button("Move Read the claim email up")).disabled).toBe(true);
    expect((await button("Move Read the claim email down")).disabled).toBe(false);
    expect((await button("Move Approve the refund down")).disabled).toBe(true);
  });

  it("puts the saved order back and says why when the API rejects the reorder (criterion 3)", async () => {
    const reason = "step_ids must list every step of the process exactly once";
    fakeApi({
      ...frame,
      [`GET ${PATH}`]: { body: processRead({ steps: THREE }) },
      [`PUT ${PATH}/steps/order`]: {
        status: 400,
        body: { detail: reason, code: "bad_request" },
        delay: 20,
      },
    });
    renderProcess();

    const down = await screen.findByRole("button", { name: "Move Read the claim email down" });
    down.focus();
    fireEvent.click(down);

    await waitFor(() =>
      expect(stepNames()).toEqual([
        "Check the warranty",
        "Read the claim email",
        "Approve the refund",
      ]),
    );
    await waitFor(() => expect(screen.getByRole("status").textContent).toBe(reason));
    expect(stepNames()).toEqual([
      "Read the claim email",
      "Check the warranty",
      "Approve the refund",
    ]);
    expect(screen.getByText("Process · v1")).toBeDefined();
    expect(document.activeElement).toBe(
      screen.getByRole("button", { name: "Move Read the claim email down" }),
    );
  });
});

describe("RS-91: deleting a step", () => {
  it("names the step in a confirmation, then updates the list and the version (criterion 2)", async () => {
    const calls = fakeApi({
      ...frame,
      [`GET ${PATH}`]: { body: processRead({ steps: THREE }) },
      [`DELETE /steps/${STEP_B!.id}`]: { body: stored([STEP_A, STEP_C!]) },
    });
    renderProcess();

    fireEvent.click(await screen.findByRole("button", { name: "Delete Check the warranty" }));
    const question = screen.getByRole("group", {
      name: "Delete step “Check the warranty”? This cannot be undone.",
    });
    expect(calls).not.toContain(`DELETE /steps/${STEP_B!.id}`);

    fireEvent.click(within(question).getByRole("button", { name: "Delete step" }));

    expect(await screen.findByText("Process · v2")).toBeDefined();
    expect(calls).toContain(`DELETE /steps/${STEP_B!.id}`);
    expect(stepNames()).toEqual(["Read the claim email", "Approve the refund"]);
    expect(within(stepRows()[1]!).getByText("02")).toBeDefined();
    await waitFor(() =>
      expect(screen.getByRole("status").textContent).toBe("Deleted “Check the warranty”."),
    );
  });

  it("keeps the step when the confirmation is withdrawn, with focus back on Delete", async () => {
    const calls = fakeApi({ ...frame, [`GET ${PATH}`]: { body: processRead({ steps: THREE }) } });
    renderProcess();

    const remove = await screen.findByRole("button", { name: "Delete Check the warranty" });
    fireEvent.click(remove);
    expect(remove.getAttribute("aria-expanded")).toBe("true");
    fireEvent.click(screen.getByRole("button", { name: "Keep it" }));

    expect(screen.queryByRole("group", { name: /Delete step/ })).toBeNull();
    expect(document.activeElement).toBe(remove);
    expect(stepNames()).toHaveLength(3);
    expect(calls.some((call) => call.startsWith("DELETE"))).toBe(false);
  });
});
