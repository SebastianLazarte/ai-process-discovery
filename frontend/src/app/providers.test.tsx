// RS-71: errors from the API reach the person, on the field for a 422 and in a toast otherwise.
import { useMutation } from "@tanstack/react-query";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { useForm } from "react-hook-form";
import { afterEach, describe, expect, it, vi } from "vitest";

import { ApiError, api, applyFieldErrors, unwrap } from "@/lib/api";

import { Providers } from "./providers";

type Values = { name: string };

// The smallest real form: react-hook-form, a TanStack mutation and the typed client.
function ProcessForm() {
  const {
    register,
    handleSubmit,
    setError,
    formState: { errors },
  } = useForm<Values>({ defaultValues: { name: "" } });
  const create = useMutation({
    mutationFn: ({ name }: Values) =>
      unwrap(api.POST("/processes", { body: { name, description: "", executions_per_month: 10 } })),
    onError: (error) => {
      if (error instanceof ApiError) applyFieldErrors(error, setError, ["name"]);
    },
  });
  return (
    <form onSubmit={handleSubmit((values) => create.mutate(values))}>
      <label htmlFor="name">Name</label>
      <input
        id="name"
        aria-invalid={errors.name ? true : undefined}
        aria-describedby={errors.name ? "name-error" : undefined}
        {...register("name")}
      />
      {errors.name && <p id="name-error">{errors.name.message}</p>}
      <button type="submit">Create process</button>
    </form>
  );
}

function respond(status: number, body: unknown) {
  const fetch = vi.fn<(request: Request) => Promise<Response>>(async () =>
    Response.json(body, { status }),
  );
  vi.stubGlobal("fetch", fetch);
  return fetch;
}

function submit() {
  render(
    <Providers>
      <ProcessForm />
    </Providers>,
  );
  fireEvent.click(screen.getByRole("button", { name: "Create process" }));
}

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

describe("RS-71: a 422 for one field", () => {
  it("shows the error on that field, and no toast", async () => {
    const fetch = respond(422, { detail: [{ loc: ["body", "name"], msg: "Name is required" }] });
    submit();

    const field = screen.getByRole("textbox", { name: "Name" });
    await waitFor(() => expect(field.getAttribute("aria-invalid")).toBe("true"));
    expect(document.getElementById(field.getAttribute("aria-describedby") ?? "")?.textContent).toBe(
      "Name is required",
    );
    expect(screen.getByRole("status").textContent).toBe("");
    const request = fetch.mock.calls[0]?.[0];
    expect(request?.method).toBe("POST");
    expect(new URL(request?.url ?? "").pathname).toBe("/api/processes");
  });
});

describe("RS-71: any other error", () => {
  it("shows the API message in a toast", async () => {
    respond(409, { detail: "This process changed meanwhile. Reload it.", code: "conflict" });
    submit();

    await waitFor(() =>
      expect(screen.getByRole("status").textContent).toBe(
        "This process changed meanwhile. Reload it.",
      ),
    );
    expect(screen.getByRole("textbox", { name: "Name" }).getAttribute("aria-invalid")).toBeNull();
  });

  it("says so in a toast when the API cannot be reached", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => {
        throw new TypeError("network down");
      }),
    );
    submit();

    await waitFor(() =>
      expect(screen.getByRole("status").textContent).toBe(
        "The API cannot be reached. Is the server running?",
      ),
    );
  });
});
