// RS-73: open a process and delete it after a confirmation that names it.
import { cleanup, fireEvent, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { fakeApi, summary } from "@/test/fake-api";
import { push, renderWithProviders } from "@/test/render";

import { ProcessView } from "./process-view";

vi.mock("next/navigation", async () => ({ useRouter: () => ({ push }) }));

const PROCESS = {
  ...summary(),
  description: "Installers send claims by email.",
  hourly_cost: null,
  created_at: "2026-10-16T09:00:00Z",
  steps: [],
};
const PATH = `/processes/${PROCESS.id}`;

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
  push.mockReset();
});

describe("a process page", () => {
  it("shows the process, with an unknown hourly cost as unknown", async () => {
    fakeApi({ [`GET ${PATH}`]: { body: PROCESS } });
    renderWithProviders(<ProcessView id={PROCESS.id} />);

    expect(await screen.findByRole("heading", { level: 1, name: PROCESS.name })).toBeDefined();
    expect(screen.getByText("Hourly cost").nextElementSibling?.textContent).toBe("unknown");
  });

  it("deletes the process only after a second, explicit confirmation", async () => {
    const calls = fakeApi({
      [`GET ${PATH}`]: { body: PROCESS },
      [`DELETE ${PATH}`]: { status: 204 },
      "GET /processes": { body: [] },
    });
    renderWithProviders(<ProcessView id={PROCESS.id} />);

    fireEvent.click(await screen.findByRole("button", { name: "Delete process" }));
    expect(calls).not.toContain(`DELETE ${PATH}`);
    expect(screen.getByText(/and all its analyses\? This cannot be undone\./)).toBeDefined();

    fireEvent.click(screen.getByRole("button", { name: "Delete for good" }));
    await waitFor(() => expect(push).toHaveBeenCalledWith("/"));
    expect(calls).toContain(`DELETE ${PATH}`);
    expect(screen.getByRole("status").textContent).toBe(`Deleted “${PROCESS.name}”.`);
  });

  it("says the process does not exist when the API answers 404", async () => {
    fakeApi({ [`GET ${PATH}`]: { status: 404, body: { detail: "process not found" } } });
    renderWithProviders(<ProcessView id={PROCESS.id} />);

    expect(
      await screen.findByRole("heading", { name: "This process does not exist" }),
    ).toBeDefined();
  });
});
