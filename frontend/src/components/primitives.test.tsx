// The shared primitives: form fields, badge, meter and dialog, by role and name.
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { afterEach, describe, expect, it } from "vitest";

import { LEVELS } from "@/lib/format/options";

import { Badge, toneOf } from "./badge";
import { Dialog } from "./dialog";
import { CheckboxField, NumberField, SelectField, TextField } from "./field";
import { Meter } from "./meter";

afterEach(cleanup);

type Values = { name: string; minutes: string; level: string; sensitive: boolean };

function Form({ error, level = "UNKNOWN" }: { error?: string; level?: string }) {
  const { register } = useForm<Values>({
    defaultValues: { name: "", minutes: "5", level, sensitive: false },
  });
  return (
    <form>
      <TextField id="name" label="Name" required error={error} register={register("name")} />
      <NumberField
        id="minutes"
        label="Minutes"
        hint="Per execution."
        register={register("minutes")}
      />
      <SelectField
        id="level"
        label="Repetitiveness"
        options={LEVELS}
        current={level}
        register={register("level")}
      />
      <CheckboxField
        id="sensitive"
        label="Handles sensitive data"
        register={register("sensitive")}
      />
    </form>
  );
}

describe("fields", () => {
  it("label each control and mark the required one", () => {
    render(<Form />);

    const name = screen.getByRole("textbox", { name: /^Name\s*\(required\)$/ });
    expect(name.getAttribute("aria-required")).toBe("true");
    expect(name.getAttribute("aria-invalid")).toBeNull();
    const minutes = screen.getByRole("textbox", { name: "Minutes" });
    expect(minutes.getAttribute("inputmode")).toBe("decimal");
    expect(document.getElementById(minutes.getAttribute("aria-describedby")!)?.textContent).toBe(
      "Per execution.",
    );
    expect(screen.getByRole("checkbox", { name: "Handles sensitive data" })).toBeDefined();
  });

  it("tie an error to its control", () => {
    render(<Form error="Field required" />);

    const name = screen.getByRole("textbox", { name: /^Name\s*\(required\)$/ });
    expect(name.getAttribute("aria-invalid")).toBe("true");
    expect(document.getElementById(name.getAttribute("aria-describedby")!)?.textContent).toBe(
      "Field required",
    );
  });

  it("offer every option with its label, the honest default selected", () => {
    render(<Form />);

    const select = screen.getByRole("combobox", { name: "Repetitiveness" }) as HTMLSelectElement;
    expect(screen.getAllByRole("option").map((option) => option.textContent)).toEqual([
      "Unknown",
      "Low",
      "Medium",
      "High",
    ]);
    expect(select.value).toBe("UNKNOWN");
  });

  it("keep a value the list does not name, so saving never swaps it", () => {
    render(<Form level="EXTREME" />);

    const select = screen.getByRole("combobox", { name: "Repetitiveness" }) as HTMLSelectElement;
    expect(select.value).toBe("EXTREME");
    expect(screen.getByRole("option", { name: "Extreme" })).toBeDefined();
  });
});

describe("badge", () => {
  it.each([
    ["RULE_BASED", "good"],
    ["AI_CANDIDATE", "info"],
    ["RECOMMENDED", "warn"],
    ["REQUIRED", "bad"],
    ["MANUAL", "bad"],
    ["PARTIAL", "neutral"],
    [null, "neutral"],
  ])("gives %s the %s tone", (value, tone) => {
    expect(toneOf(value)).toBe(tone);
  });

  it("prints the label of its value, or its own text", () => {
    render(
      <>
        <Badge value="API_INTEGRATION" />
        <Badge value="REQUIRED">Control: Required</Badge>
      </>,
    );
    expect(screen.getByText("API integration")).toBeDefined();
    expect(screen.getByText("Control: Required").getAttribute("data-tone")).toBe("bad");
  });
});

describe("meter", () => {
  it("places the score the API returned, with a name", () => {
    render(<Meter value="64" label="Suitability score" />);

    const meter = screen.getByRole("meter", { name: "Suitability score" });
    expect(meter.getAttribute("value")).toBe("64");
    expect(meter.getAttribute("max")).toBe("100");
    expect(meter.getAttribute("style")).toBeNull();
  });
});

describe("dialog", () => {
  function Opener() {
    const [open, setOpen] = useState(false);
    return (
      <>
        <button type="button" onClick={() => setOpen(true)}>
          Open
        </button>
        <p>{open ? "open" : "closed"}</p>
        <Dialog open={open} onClose={() => setOpen(false)} title="Override this step">
          <button type="button" onClick={() => setOpen(false)}>
            Cancel
          </button>
        </Dialog>
      </>
    );
  }

  it("opens on demand, named by its title, and closes", () => {
    render(<Opener />);
    expect(screen.queryByRole("dialog")).toBeNull();

    fireEvent.click(screen.getByRole("button", { name: "Open" }));
    expect(screen.getByRole("dialog", { name: "Override this step" })).toBeDefined();

    fireEvent.click(screen.getByRole("button", { name: "Cancel" }));
    expect(screen.queryByRole("dialog")).toBeNull();
    expect(screen.getByText("closed")).toBeDefined();
  });
});
