// RS-73, criterion 3: on the public demo, every page warns that data is public and deleted daily.
import { cleanup, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { fakeApi } from "@/test/fake-api";
import { renderWithProviders } from "@/test/render";

import { AppShell } from "./app-shell";

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

describe("the app shell", () => {
  it("shows the public demo banner around any page", async () => {
    fakeApi({ "GET /meta": { body: { version: "1.3.1", public_demo: true } } });
    renderWithProviders(
      <AppShell>
        <h1>Any page</h1>
      </AppShell>,
    );

    const banner = await screen.findByRole("note");
    expect(banner.textContent).toContain("visible to other visitors and deleted daily");
    expect(screen.getByRole("heading", { name: "Any page" })).toBeDefined();
  });

  it("shows no banner outside the public demo", async () => {
    const calls = fakeApi({ "GET /meta": { body: { version: "1.3.1", public_demo: false } } });
    renderWithProviders(<AppShell>page</AppShell>);

    await vi.waitFor(() => expect(calls).toContain("GET /meta"));
    expect(screen.queryByRole("note")).toBeNull();
  });

  it("offers a skip link to the main content", () => {
    fakeApi({ "GET /meta": { body: { version: "1.3.1", public_demo: false } } });
    renderWithProviders(<AppShell>page</AppShell>);

    expect(screen.getByRole("link", { name: "Skip to content" }).getAttribute("href")).toBe(
      "#main",
    );
    expect(screen.getByRole("main").id).toBe("main");
  });
});
