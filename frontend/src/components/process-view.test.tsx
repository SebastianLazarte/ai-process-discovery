// RS-73: open a process. The frame of every process page: its title, its tabs, and a clear
// page when the process does not exist.
import { cleanup, screen, within } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { fakeApi } from "@/test/fake-api";
import { ANALYSIS_ID, analysisSummary, processRead } from "@/test/fixtures";
import { push, renderWithProviders } from "@/test/render";

import { ProcessView } from "./process-view";

const pathname = vi.hoisted(() => ({ current: "/" }));
vi.mock("next/navigation", async () => ({
  useRouter: () => ({ push }),
  usePathname: () => pathname.current,
}));

const PROCESS = processRead();
const PATH = `/processes/${PROCESS.id}`;

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
  push.mockReset();
  pathname.current = "/";
});

function api(analyses: unknown[] = []) {
  return fakeApi({
    [`GET ${PATH}`]: { body: PROCESS },
    [`GET ${PATH}/analyses`]: { body: analyses },
  });
}

describe("a process page", () => {
  it("shows the process and its section", async () => {
    pathname.current = PATH;
    api();
    renderWithProviders(
      <ProcessView id={PROCESS.id}>
        <h2>Section</h2>
      </ProcessView>,
    );

    expect(await screen.findByRole("heading", { level: 1, name: PROCESS.name })).toBeDefined();
    expect(screen.getByText("Process · v1")).toBeDefined();
    expect(screen.getByRole("heading", { level: 2, name: "Section" })).toBeDefined();
  });

  it("says the process does not exist when the API answers 404, and shows no section", async () => {
    fakeApi({ [`GET ${PATH}`]: { status: 404, body: { detail: "process not found" } } });
    renderWithProviders(
      <ProcessView id={PROCESS.id}>
        <h2>Section</h2>
      </ProcessView>,
    );

    expect(
      await screen.findByRole("heading", { name: "This process does not exist" }),
    ).toBeDefined();
    expect(screen.queryByRole("heading", { name: "Section" })).toBeNull();
    expect(screen.queryByRole("navigation", { name: "Process sections" })).toBeNull();
  });
});

describe("the process tabs", () => {
  it("disable Results and Blueprint until an analysis exists, and say why", async () => {
    pathname.current = PATH;
    const calls = api([]);
    renderWithProviders(<ProcessView id={PROCESS.id} />);

    const tabs = await screen.findByRole("navigation", { name: "Process sections" });
    await vi.waitFor(() => expect(calls).toContain(`GET ${PATH}/analyses`));
    const steps = within(tabs).getByRole("link", { name: "Steps" });
    expect(steps.getAttribute("href")).toBe(PATH);
    expect(steps.getAttribute("aria-current")).toBe("page");
    expect(within(tabs).getByRole("link", { name: "Analyse" }).getAttribute("href")).toBe(
      `${PATH}/analyse`,
    );
    expect(within(tabs).getByRole("link", { name: "History" }).getAttribute("href")).toBe(
      `${PATH}/history`,
    );
    for (const name of ["Results", "Blueprint"]) {
      const tab = within(tabs).getByRole("link", { name });
      expect(tab.getAttribute("aria-disabled")).toBe("true");
      expect(tab.getAttribute("href")).toBeNull();
      const why = document.getElementById(tab.getAttribute("aria-describedby") ?? "");
      expect(why?.textContent).toBe("Run an analysis first");
    }
  });

  it("open the latest analysis once there is one", async () => {
    pathname.current = `${PATH}/history`;
    const older = analysisSummary({ id: "77777777-7777-4777-8777-777777777777" });
    api([analysisSummary(), older]);
    renderWithProviders(<ProcessView id={PROCESS.id} />);

    const tabs = await screen.findByRole("navigation", { name: "Process sections" });
    const results = () => within(tabs).getByRole("link", { name: "Results" });
    await vi.waitFor(() =>
      expect(results().getAttribute("href")).toBe(`${PATH}/analyses/${ANALYSIS_ID}`),
    );
    expect(within(tabs).getByRole("link", { name: "Blueprint" }).getAttribute("href")).toBe(
      `${PATH}/analyses/${ANALYSIS_ID}/blueprint`,
    );
    expect(results().getAttribute("aria-disabled")).toBeNull();
    expect(within(tabs).getByRole("link", { name: "History" }).getAttribute("aria-current")).toBe(
      "page",
    );
  });

  it("follow the analysis on screen, even an older one", async () => {
    const older = "77777777-7777-4777-8777-777777777777";
    pathname.current = `${PATH}/analyses/${older}/blueprint`;
    api([analysisSummary(), analysisSummary({ id: older })]);
    renderWithProviders(<ProcessView id={PROCESS.id} />);

    const tabs = await screen.findByRole("navigation", { name: "Process sections" });
    const blueprint = within(tabs).getByRole("link", { name: "Blueprint" });
    expect(blueprint.getAttribute("href")).toBe(`${PATH}/analyses/${older}/blueprint`);
    expect(blueprint.getAttribute("aria-current")).toBe("page");
    expect(within(tabs).getByRole("link", { name: "Results" }).getAttribute("href")).toBe(
      `${PATH}/analyses/${older}`,
    );
  });
});
