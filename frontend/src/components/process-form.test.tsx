// RS-73: create a process; an unknown hourly cost travels as null, never as zero.
import { cleanup, fireEvent, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { fakeApi, summary } from "@/test/fake-api";
import { push, renderWithProviders } from "@/test/render";

import { ProcessForm } from "./process-form";

vi.mock("next/navigation", async () => ({ useRouter: () => ({ push }) }));

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
  push.mockReset();
});

function type(label: string, value: string) {
  fireEvent.change(screen.getByLabelText(label, { exact: false }), { target: { value } });
}

describe("creating a process", () => {
  it("sends the form and opens the new process", async () => {
    const created = summary({ id: "33333333-3333-4333-8333-333333333333", name: "Quote approval" });
    let sent: unknown;
    fakeApi({
      "POST /processes": async (request) => {
        sent = await request.json();
        return { status: 201, body: { ...created, steps: [] } };
      },
    });
    renderWithProviders(<ProcessForm />);

    type("Name", "Quote approval");
    type("Executions per month", "40");
    fireEvent.click(screen.getByRole("button", { name: "Create process" }));

    await waitFor(() => expect(push).toHaveBeenCalledWith(`/processes/${created.id}`));
    expect(sent).toEqual({
      name: "Quote approval",
      owner: null,
      executions_per_month: "40",
      hourly_cost: null,
      description: "",
    });
  });

  it("shows a validation error on its field", async () => {
    fakeApi({
      "POST /processes": {
        status: 422,
        body: { detail: [{ loc: ["body", "executions_per_month"], msg: "Must be at least 1" }] },
      },
    });
    renderWithProviders(<ProcessForm />);

    type("Executions per month", "0");
    fireEvent.click(screen.getByRole("button", { name: "Create process" }));

    const field = screen.getByLabelText("Executions per month", { exact: false });
    await waitFor(() => expect(field.getAttribute("aria-invalid")).toBe("true"));
    expect(screen.getByText("Must be at least 1")).toBeDefined();
    expect(push).not.toHaveBeenCalled();
  });
});
