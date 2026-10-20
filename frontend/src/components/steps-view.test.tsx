// RS-73: the Steps tab shows the facts of the process, an unknown hourly cost as unknown,
// and deletes the process after a confirmation that names it. RS-74: it lists the steps in
// order and saves the process settings.
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
  it("shows each step's position, name, minutes and occurrence rate, in order (RS-74, criterion 1)", async () => {
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
