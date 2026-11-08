// RS-73, criterion 3: on the public demo, every page warns that data is public and deleted
// daily. Plus the shell around every page: skip link and the navigation in two forms,
// the full sidebar on Home and a rail inside a process (RS-105, ADR 0018).
import { cleanup, fireEvent, screen, within } from "@testing-library/react";
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

describe("RS-109.1: the slim demo banner", () => {
  it("is one line with a status dot and keeps the full text of RS-62", async () => {
    api(true);
    renderWithProviders(<AppShell>page</AppShell>);

    const banner = await screen.findByRole("note");
    expect(banner.textContent).toBe(
      "Public demo v1.3.1. Anything you enter is visible to other visitors and deleted daily. Do not enter real or personal data.",
    );
    expect(banner.querySelector("br, p, div")).toBeNull();
    const dot = banner.firstElementChild;
    expect(dot?.getAttribute("aria-hidden")).toBe("true");
    expect(dot?.textContent).toBe("");
  });
});

describe("the navigation", () => {
  it("RS-105.1: Home shows the full sidebar with the brand, New process and every process", async () => {
    pathname.current = "/";
    api(false);
    renderWithProviders(<AppShell>page</AppShell>);

    expect(screen.getByRole("link", { name: /Process Discovery/ }).getAttribute("href")).toBe("/");
    expect(screen.getByRole("link", { name: "New process" }).getAttribute("href")).toBe(
      "/processes/new",
    );
    const nav = screen.getByRole("navigation", { name: "Processes" });
    expect(await within(nav).findByRole("link", { name: /Order intake/ })).toBeDefined();
    expect(within(nav).getByRole("link", { name: new RegExp(OTHER.name) })).toBeDefined();
    expect(screen.queryByRole("button", { name: "Processes" })).toBeNull();
  });

  it("RS-105.1: New process keeps the full sidebar, with no process marked", async () => {
    pathname.current = "/processes/new";
    api(false);
    renderWithProviders(<AppShell>page</AppShell>);

    const nav = screen.getByRole("navigation", { name: "Processes" });
    const links = await within(nav).findAllByRole("link");
    expect(links.map((link) => link.getAttribute("aria-current"))).toEqual([null, null]);
  });

  it("RS-105.2: a process page shows a rail of named icons instead of the sidebar", async () => {
    pathname.current = `/processes/${CURRENT.id}/analyse`;
    const calls = api(false);
    renderWithProviders(<AppShell>page</AppShell>);

    const rail = screen.getByRole("list", { name: "Navigation" });
    const controls = [
      ...within(rail).getAllByRole("link"),
      ...within(rail).getAllByRole("button"),
    ].map((control) => control.getAttribute("aria-label"));
    expect(controls).toEqual(["Home", "New process", "Processes"]);
    expect(within(rail).getByRole("link", { name: "New process" }).getAttribute("href")).toBe(
      "/processes/new",
    );
    expect(screen.queryByText("Process Discovery")).toBeNull();
    await vi.waitFor(() => expect(calls).toContain("GET /processes"));
    expect(screen.queryByRole("navigation", { name: "Processes" })).toBeNull();
  });

  it("RS-105.2: the process list opens from the rail with the current process marked", async () => {
    pathname.current = `/processes/${CURRENT.id}/analyse`;
    api(false);
    renderWithProviders(<AppShell>page</AppShell>);

    const toggle = screen.getByRole("button", { name: "Processes" });
    expect(toggle.getAttribute("aria-expanded")).toBe("false");
    fireEvent.click(toggle);

    expect(toggle.getAttribute("aria-expanded")).toBe("true");
    const nav = screen.getByRole("navigation", { name: "Processes" });
    const current = await within(nav).findByRole("link", { name: /Order intake/ });
    expect(current.getAttribute("aria-current")).toBe("page");
    expect(
      within(nav)
        .getByRole("link", { name: new RegExp(OTHER.name) })
        .getAttribute("aria-current"),
    ).toBeNull();
  });

  it("RS-105.2: Escape closes the process list and returns focus to the rail", () => {
    pathname.current = `/processes/${CURRENT.id}`;
    api(false);
    renderWithProviders(<AppShell>page</AppShell>);

    const toggle = screen.getByRole("button", { name: "Processes" });
    fireEvent.click(toggle);
    fireEvent.keyDown(document, { key: "Escape" });

    expect(toggle.getAttribute("aria-expanded")).toBe("false");
    expect(screen.queryByRole("navigation", { name: "Processes" })).toBeNull();
    expect(document.activeElement).toBe(toggle);
  });

  it("RS-105.2: a click outside the rail closes the process list", () => {
    pathname.current = `/processes/${CURRENT.id}`;
    api(false);
    renderWithProviders(
      <AppShell>
        <h1>Results</h1>
      </AppShell>,
    );

    const toggle = screen.getByRole("button", { name: "Processes" });
    fireEvent.click(toggle);
    fireEvent.pointerDown(screen.getByRole("heading", { name: "Results" }));

    expect(toggle.getAttribute("aria-expanded")).toBe("false");
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
