// RS-73, criterion 3: on the public demo, every page warns that data is public and deleted
// daily. Plus the shell around every page: skip link and the sidebar (ADR 0014).
import { cleanup, screen, within } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { fakeApi, summary } from "@/test/fake-api";
import { renderWithProviders } from "@/test/render";

import { AppShell } from "./app-shell";

const pathname = vi.hoisted(() => ({ current: "/" }));
vi.mock("next/navigation", async () => ({ usePathname: () => pathname.current }));

const CURRENT = summary({ id: "44444444-4444-4444-8444-444444444444", name: "Order intake" });
const OTHER = summary();

function api(publicDemo: boolean) {
  return fakeApi({
    "GET /meta": { body: { version: "1.3.1", public_demo: publicDemo } },
    "GET /processes": { body: [CURRENT, OTHER] },
  });
}

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
  pathname.current = "/";
});

describe("the public demo banner", () => {
  it("shows around any page", async () => {
    api(true);
    renderWithProviders(
      <AppShell>
        <h1>Any page</h1>
      </AppShell>,
    );

    const banner = await screen.findByRole("note");
    expect(banner.textContent).toContain("visible to other visitors and deleted daily");
    expect(screen.getByRole("heading", { name: "Any page" })).toBeDefined();
  });

  it("stays hidden outside the public demo", async () => {
    const calls = api(false);
    renderWithProviders(<AppShell>page</AppShell>);

    await vi.waitFor(() => expect(calls).toContain("GET /meta"));
    expect(screen.queryByRole("note")).toBeNull();
  });
});

describe("the sidebar", () => {
  it("lists every process and marks the one on screen", async () => {
    pathname.current = `/processes/${CURRENT.id}`;
    api(false);
    renderWithProviders(<AppShell>page</AppShell>);

    const nav = screen.getByRole("navigation", { name: "Processes" });
    const current = await within(nav).findByRole("link", { name: /Order intake/ });
    expect(current.getAttribute("aria-current")).toBe("page");
    expect(
      within(nav)
        .getByRole("link", { name: new RegExp(OTHER.name) })
        .getAttribute("aria-current"),
    ).toBeNull();
    expect(screen.getByRole("link", { name: "+ New process" }).getAttribute("href")).toBe(
      "/processes/new",
    );
  });
});

describe("the skip link", () => {
  it("leads to the main content", () => {
    api(false);
    renderWithProviders(<AppShell>page</AppShell>);

    expect(screen.getByRole("link", { name: "Skip to content" }).getAttribute("href")).toBe(
      "#main",
    );
    expect(screen.getByRole("main").id).toBe("main");
  });
});
