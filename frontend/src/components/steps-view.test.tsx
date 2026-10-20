// RS-73: the Steps tab shows the facts of the process, an unknown hourly cost as unknown,
// and deletes the process after a confirmation that names it.
import { cleanup, fireEvent, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { fakeApi } from "@/test/fake-api";
import { processRead } from "@/test/fixtures";
import { push, renderWithProviders } from "@/test/render";

import { StepsView } from "./steps-view";

vi.mock("next/navigation", async () => ({ useRouter: () => ({ push }) }));

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

    expect((await screen.findByText("Hourly cost")).nextElementSibling?.textContent).toBe(
      "unknown",
    );
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
