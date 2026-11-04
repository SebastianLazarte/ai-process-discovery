// Our own icons (ADR 0018): no icon package, and every icon is hidden or named.
import { readFileSync } from "node:fs";
import { join } from "node:path";

import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import { ICONS } from "./icons";

afterEach(cleanup);

const ICON_PACKAGES =
  /lucide|react-icons|heroicons|tabler|phosphor|feather|radix-ui\/react-icons|fontawesome|material-symbols|@mui\/icons/i;

describe("RS-104.4: the icon set", () => {
  it("comes from no icon package", () => {
    const manifest = JSON.parse(
      readFileSync(join(import.meta.dirname, "..", "..", "package.json"), "utf-8"),
    ) as Record<string, Record<string, string> | undefined>;
    const names = Object.keys({ ...manifest.dependencies, ...manifest.devDependencies });
    expect(names.filter((name) => ICON_PACKAGES.test(name))).toEqual([]);
  });

  it.each(Object.entries(ICONS))("%s is hidden from screen readers beside its text", (_, Icon) => {
    const { container } = render(<Icon />);
    const svg = container.querySelector("svg")!;
    expect(svg.getAttribute("aria-hidden")).toBe("true");
    expect(screen.queryByRole("img")).toBeNull();
  });

  it.each(Object.entries(ICONS))("%s carries a name when it stands alone", (_, Icon) => {
    render(<Icon label="Download blueprint" />);
    expect(screen.getByRole("img", { name: "Download blueprint" })).toBeDefined();
  });
});
