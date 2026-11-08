// Graphite buttons (ADR 0018): one filled primary, every variant with the same states.
import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import { Button, buttonClass, type ButtonVariant } from "./button";

afterEach(cleanup);

const VARIANTS: ButtonVariant[] = ["primary", "secondary", "tertiary", "danger"];

describe("RS-104.3: button states", () => {
  it.each(VARIANTS)("%s has hover, focus-visible, disabled and pending styles", (variant) => {
    const classes = buttonClass(variant).split(" ");
    for (const state of ["hover:", "focus-visible:", "disabled:", "aria-busy:"]) {
      expect(classes.some((name) => name.startsWith(state))).toBe(true);
    }
  });

  it("fills only the primary with the accent", () => {
    const filled = VARIANTS.filter((variant) =>
      buttonClass(variant).split(" ").includes("bg-accent"),
    );
    expect(filled).toEqual(["primary"]);
  });

  it.each(VARIANTS)("%s renders enabled, then disabled", (variant) => {
    const { rerender } = render(<Button variant={variant}>Save</Button>);
    const button = screen.getByRole("button", { name: "Save" });
    expect(button.hasAttribute("disabled")).toBe(false);
    expect(button.getAttribute("aria-busy")).toBeNull();

    rerender(
      <Button variant={variant} disabled>
        Save
      </Button>,
    );
    expect(screen.getByRole("button", { name: "Save" }).hasAttribute("disabled")).toBe(true);
  });

  it.each(VARIANTS)("%s says it is busy and stops a second click while pending", (variant) => {
    render(
      <Button variant={variant} pending pendingLabel="Saving…">
        Save
      </Button>,
    );
    const button = screen.getByRole("button", { name: "Saving…" });
    expect(button.getAttribute("aria-busy")).toBe("true");
    expect(button.hasAttribute("disabled")).toBe(true);
  });

  it("submits a form only when asked to", () => {
    render(
      <>
        <Button>Cancel</Button>
        <Button type="submit" variant="primary">
          Run analysis
        </Button>
      </>,
    );
    expect(screen.getByRole("button", { name: "Cancel" }).getAttribute("type")).toBe("button");
    expect(screen.getByRole("button", { name: "Run analysis" }).getAttribute("type")).toBe(
      "submit",
    );
  });
});
