// RS-108: what makes a screen Graphite (ADR 0018), checked on the rendered page. Each check
// reads the classes that the primitives of RS-104 set, so a screen that rolls its own
// control or surface fails here.
import { expect } from "vitest";

const classes = (element: Element) => (element.getAttribute("class") ?? "").split(/\s+/);

/**
 * Every button is a Graphite button, at most one control is filled with the accent, no
 * surface draws a full border, and no note keeps the left border of the vanilla client.
 */
export function expectGraphite(root: HTMLElement): void {
  const buttons = [...root.querySelectorAll("button")];
  for (const button of buttons) {
    expect(classes(button), `button "${button.textContent}"`).toEqual(
      expect.arrayContaining(["rounded-control", "focus-visible:outline-accent"]),
    );
  }

  const filled = [...root.querySelectorAll("a, button")].filter((control) =>
    classes(control).includes("bg-accent"),
  );
  expect(filled.length, "filled primary actions").toBeLessThanOrEqual(1);

  const bordered = [...root.querySelectorAll("[class]")].filter((element) => {
    const names = classes(element);
    return names.includes("border") && names.includes("border-line");
  });
  expect(
    bordered.map((element) => element.tagName),
    "surfaces with a full border",
  ).toEqual([]);

  const leftBorders = [...root.querySelectorAll("[class]")].filter((element) =>
    classes(element).some((name) => name.startsWith("border-l-")),
  );
  expect(leftBorders.length, "notes with a left border").toBe(0);
}
