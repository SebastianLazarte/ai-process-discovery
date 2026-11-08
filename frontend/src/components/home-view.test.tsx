// RS-73, criteria 1 and 2: load a demo from the list, and names always render as text.
// RS-92, criterion 5: a demo that comes with its first analysis opens its Results.
// RS-106: three ways to start, one primary action, demo figures only from the API.
import { cleanup, fireEvent, screen, waitFor, within } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { fakeApi, summary } from "@/test/fake-api";
import { ANALYSIS_ID, analysisSummary } from "@/test/fixtures";
import { push, renderWithProviders } from "@/test/render";

import { AppShell } from "./app-shell";
import { HomeView } from "./home-view";

vi.mock("next/navigation", async () => ({
  useRouter: () => ({ push }),
  usePathname: () => "/",
}));

const META = { version: "2.1.0", public_demo: false, process_drafts_enabled: false };

const DEMO = {
  slug: "warranty-claims",
  name: "Warranty claims from installers",
  description: "Installers send warranty claims by email.",
  step_count: 7,
  executions_per_month: 1320,
};

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
  push.mockReset();
});

describe("RS-73.1: loading a demo", () => {
  it("adds it to the list and opens it", async () => {
    const loaded = summary({ id: "22222222-2222-4222-8222-222222222222", name: DEMO.name });
    let stored: unknown[] = [];
    const calls = fakeApi({
      "GET /meta": { body: META },
      "GET /demo-processes": { body: [DEMO] },
      "GET /processes": () => ({ body: stored }),
      "POST /demo-processes/warranty-claims": () => {
        stored = [loaded];
        return { status: 201, body: { ...loaded, steps: [] } };
      },
      [`GET /processes/${loaded.id}/analyses`]: { body: [] },
    });
    renderWithProviders(<HomeView />);

    expect(await screen.findByRole("heading", { name: "No processes yet" })).toBeDefined();
    fireEvent.click(await screen.findByRole("button", { name: `Load and open: ${DEMO.name}` }));

    const table = await screen.findByRole("table", { name: "Your processes" });
    expect(within(table).getByRole("link", { name: DEMO.name })).toBeDefined();
    await waitFor(() => expect(push).toHaveBeenCalledWith(`/processes/${loaded.id}`));
    expect(calls).toContain("POST /demo-processes/warranty-claims");
  });
});

describe("RS-92.5: loading a demo with its first analysis", () => {
  it("opens the Results of that analysis", async () => {
    const loaded = summary({ id: "22222222-2222-4222-8222-222222222222", name: DEMO.name });
    fakeApi({
      "GET /meta": { body: META },
      "GET /demo-processes": { body: [DEMO] },
      "GET /processes": { body: [] },
      "POST /demo-processes/warranty-claims": { status: 201, body: { ...loaded, steps: [] } },
      [`GET /processes/${loaded.id}/analyses`]: { body: [analysisSummary()] },
    });
    renderWithProviders(<HomeView />);

    fireEvent.click(await screen.findByRole("button", { name: `Load and open: ${DEMO.name}` }));

    await waitFor(() =>
      expect(push).toHaveBeenCalledWith(`/processes/${loaded.id}/analyses/${ANALYSIS_ID}`),
    );
  });
});

describe("a process name with markup", () => {
  it("shows as text and adds no element", async () => {
    const name = "<img src=x onerror=alert(1)>";
    fakeApi({
      "GET /meta": { body: META },
      "GET /demo-processes": { body: [] },
      "GET /processes": { body: [summary({ name })] },
    });
    const { container } = renderWithProviders(<HomeView />);

    expect(await screen.findByText(name)).toBeDefined();
    expect(container.querySelector("img")).toBeNull();
  });
});

describe("RS-106: three ways to start", () => {
  function home(drafts: boolean, demos: unknown[] = [DEMO]) {
    fakeApi({
      "GET /meta": { body: { ...META, process_drafts_enabled: drafts } },
      "GET /demo-processes": { body: demos },
      "GET /processes": { body: [] },
    });
    return renderWithProviders(
      <AppShell>
        <HomeView />
      </AppShell>,
    );
  }

  it("RS-106.1: offers your sector, your own words and a demo, with one primary action", async () => {
    home(true);

    const ways = screen.getByRole("list", { name: "Ways to start" });
    expect(
      await within(ways).findByRole("link", { name: /^Describe it in your words/ }),
    ).toBeDefined();
    const links = within(ways).getAllByRole("link");
    expect(links.map((link) => link.getAttribute("href"))).toEqual([
      "/processes/new",
      "/processes/new",
      "#demos-title",
    ]);
    expect(links[0]?.textContent).toMatch(/^Start from your sector/);
    expect(links[2]?.textContent).toMatch(/^Open a demo/);

    await screen.findByRole("button", { name: `Load and open: ${DEMO.name}` });
    const filled = [...screen.getAllByRole("link"), ...screen.getAllByRole("button")].filter(
      (control) => control.className.split(" ").includes("bg-accent"),
    );
    expect(filled.map((control) => control.textContent)).toEqual(["New process"]);
  });

  it("RS-106.2: hides the describe-it option while AI drafts are off", async () => {
    home(false);

    const ways = screen.getByRole("list", { name: "Ways to start" });
    await screen.findByRole("button", { name: `Load and open: ${DEMO.name}` });
    const names = within(ways)
      .getAllByRole("link")
      .map((link) => link.textContent);
    expect(names).toHaveLength(2);
    expect(names.some((name) => name?.includes("Describe it in your words"))).toBe(false);
  });

  it("RS-106.3: a demo card prints the figures the API counted, and none when it sends none", async () => {
    const bare = { slug: "bare", name: "Bare demo", description: "No figures here." };
    home(false, [DEMO, bare]);

    const demos = await screen.findByRole("list", { name: "Demos" });
    const [counted, plain] = await within(demos).findAllByRole("listitem");
    if (!counted || !plain) throw new Error("expected two demo cards");
    expect(within(counted).getByText("7 steps · 1,320 runs a month")).toBeDefined();
    expect(plain.textContent).not.toMatch(/\d/);
  });
});

describe("RS-109: empty states and skeletons on Home", () => {
  it("RS-109.2: the sidebar and Home show an empty state with a way to start", async () => {
    fakeApi({
      "GET /meta": { body: META },
      "GET /demo-processes": { body: [DEMO] },
      "GET /processes": { body: [] },
    });
    renderWithProviders(
      <AppShell>
        <HomeView />
      </AppShell>,
    );

    const nav = screen.getByRole("navigation", { name: "Processes" });
    expect(await within(nav).findByRole("heading", { name: "No processes yet" })).toBeDefined();
    expect(
      within(nav).getByRole("link", { name: "Start from your sector" }).getAttribute("href"),
    ).toBe("/processes/new");
    expect(within(nav).getByRole("link", { name: "Open a demo" }).getAttribute("href")).toBe(
      "/#demos-title",
    );

    const panel = screen.getByRole("region", { name: "Your processes" });
    expect(await within(panel).findByRole("heading", { name: "No processes yet" })).toBeDefined();
    expect(
      within(panel).getByRole("link", { name: "Start from your sector" }).getAttribute("href"),
    ).toBe("/processes/new");
    expect(within(panel).getByRole("link", { name: "Open a demo" }).getAttribute("href")).toBe(
      "#demos-title",
    );
  });

  it("RS-109.3: the demos wait in a skeleton laid out as the cards", async () => {
    fakeApi({
      "GET /meta": { body: META },
      "GET /demo-processes": { body: [DEMO], delay: 50 },
      "GET /processes": { body: [] },
    });
    renderWithProviders(<HomeView />);

    const skeleton = screen.getByRole("status", { name: "Loading demos" });
    const grid = skeleton.querySelector("[aria-hidden] > div");
    expect(grid?.children).toHaveLength(3);
    const skeletonGrid = grid?.className;

    const cards = await screen.findByRole("list", { name: "Demos" });
    expect(screen.queryByRole("status", { name: "Loading demos" })).toBeNull();
    expect(cards.className).toBe(skeletonGrid);
  });
});
