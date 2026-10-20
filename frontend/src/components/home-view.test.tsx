// RS-73, criteria 1 and 2: load a demo from the list, and names always render as text.
// RS-92, criterion 5: a demo that comes with its first analysis opens its Results.
import { cleanup, fireEvent, screen, waitFor, within } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { fakeApi, summary } from "@/test/fake-api";
import { ANALYSIS_ID, analysisSummary } from "@/test/fixtures";
import { push, renderWithProviders } from "@/test/render";

import { HomeView } from "./home-view";

vi.mock("next/navigation", async () => ({ useRouter: () => ({ push }) }));

const DEMO = {
  slug: "warranty-claims",
  name: "Warranty claims from installers",
  description: "Installers send warranty claims by email.",
};

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
  push.mockReset();
});

describe("loading a demo", () => {
  it("adds it to the list and opens it", async () => {
    const loaded = summary({ id: "22222222-2222-4222-8222-222222222222", name: DEMO.name });
    let stored: unknown[] = [];
    const calls = fakeApi({
      "GET /demo-processes": { body: [DEMO] },
      "GET /processes": () => ({ body: stored }),
      "POST /demo-processes/warranty-claims": () => {
        stored = [loaded];
        return { status: 201, body: { ...loaded, steps: [] } };
      },
      [`GET /processes/${loaded.id}/analyses`]: { body: [] },
    });
    renderWithProviders(<HomeView />);

    expect(await screen.findByText("No processes yet. Load a demo or create one.")).toBeDefined();
    fireEvent.click(await screen.findByRole("button", { name: `Load and open: ${DEMO.name}` }));

    const table = await screen.findByRole("table", { name: "Your processes" });
    expect(within(table).getByRole("link", { name: DEMO.name })).toBeDefined();
    await waitFor(() => expect(push).toHaveBeenCalledWith(`/processes/${loaded.id}`));
    expect(calls).toContain("POST /demo-processes/warranty-claims");
  });
});

describe("loading a demo with its first analysis", () => {
  it("opens the Results of that analysis", async () => {
    const loaded = summary({ id: "22222222-2222-4222-8222-222222222222", name: DEMO.name });
    fakeApi({
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
      "GET /demo-processes": { body: [] },
      "GET /processes": { body: [summary({ name })] },
    });
    const { container } = renderWithProviders(<HomeView />);

    expect(await screen.findByText(name)).toBeDefined();
    expect(container.querySelector("img")).toBeNull();
  });
});
