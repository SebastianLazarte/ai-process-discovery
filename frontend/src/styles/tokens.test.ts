// @vitest-environment node
// ADR 0013: colours live in tokens.css only. A component that writes its own colour, or
// reaches for the default Tailwind palette, fails here.
import { readFileSync, readdirSync } from "node:fs";
import { join, relative } from "node:path";

import { describe, expect, it } from "vitest";

const SRC = join(import.meta.dirname, "..");
const TOKENS = join(SRC, "styles", "tokens.css");

function sources(dir: string): string[] {
  return readdirSync(dir, { withFileTypes: true }).flatMap((entry) => {
    const path = join(dir, entry.name);
    if (entry.isDirectory()) return sources(path);
    const scanned = /\.(tsx?|css)$/.test(entry.name) && !/\.(test|d)\.tsx?$/.test(entry.name);
    return scanned && path !== TOKENS ? [path] : [];
  });
}

const LITERAL = /#[0-9a-f]{3,8}\b|\b(?:rgba?|hsla?|oklch|oklab|lab|lch)\(/gi;
const PALETTE =
  /\b(?:bg|text|border|outline|ring|divide|fill|stroke|from|to|via|accent|caret|decoration|shadow)-(?:slate|gray|zinc|neutral|stone|red|orange|amber|yellow|lime|green|emerald|teal|cyan|sky|blue|indigo|violet|purple|fuchsia|pink|rose|black|white)(?:-\d{2,3})?\b/g;

describe("design tokens", () => {
  const files = sources(SRC);

  it("scans the components and pages", () => {
    expect(files.some((file) => file.endsWith("home-view.tsx"))).toBe(true);
  });

  it.each(files.map((file) => [relative(SRC, file), file]))(
    "%s uses no colour literal and no default palette class",
    (_, file) => {
      const text = readFileSync(file, "utf-8");
      expect(text.match(LITERAL) ?? []).toEqual([]);
      expect(text.match(PALETTE) ?? []).toEqual([]);
    },
  );
});

// WCAG 2.2 AA in the dark theme: 4.5:1 for text, 3:1 for control borders and focus.
// The relative luminance is computed straight from each OKLCH token.
function tokens(): Map<string, string> {
  const css = readFileSync(TOKENS, "utf-8");
  return new Map([...css.matchAll(/--([\w-]+):\s*([^;]+);/g)].map((m) => [m[1]!, m[2]!.trim()]));
}

function luminance(name: string, all: Map<string, string>): number {
  let value = all.get(name) ?? "";
  for (let hops = 0; value.startsWith("var("); hops++) {
    if (hops > 5) throw new Error(`token ${name} does not resolve`);
    value = all.get(value.slice(6, -1)) ?? "";
  }
  const match = value.match(/oklch\(([\d.]+)% ([\d.]+) ([\d.]+)\)/);
  if (!match) throw new Error(`token ${name} is not OKLCH: ${value}`);
  const [L, C, H] = [Number(match[1]) / 100, Number(match[2]), (Number(match[3]) * Math.PI) / 180];
  const [a, b] = [C * Math.cos(H), C * Math.sin(H)];
  const l = (L + 0.3963377774 * a + 0.2158037573 * b) ** 3;
  const m = (L - 0.1055613458 * a - 0.0638541728 * b) ** 3;
  const s = (L - 0.0894841775 * a - 1.291485548 * b) ** 3;
  const r = 4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s;
  const g = -1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s;
  const bl = -0.0041960863 * l - 0.7034186147 * m + 1.707614701 * s;
  const clamp = (x: number) => Math.min(Math.max(x, 0), 1);
  return 0.2126 * clamp(r) + 0.7152 * clamp(g) + 0.0722 * clamp(bl);
}

function contrast(fg: string, bg: string): number {
  const all = tokens();
  const [x, y] = [luminance(fg, all), luminance(bg, all)].sort((p, q) => q - p);
  return (x! + 0.05) / (y! + 0.05);
}

describe("dark theme contrast", () => {
  it.each([
    ["ink", "bg", 4.5],
    ["ink", "surface", 4.5],
    ["ink", "toast-bg", 4.5],
    ["ink-soft", "sidebar", 4.5],
    ["muted", "bg", 4.5],
    ["muted", "surface", 4.5],
    ["muted", "surface-raised", 4.5],
    ["muted", "sidebar", 4.5],
    ["label", "surface", 4.5],
    ["table-head", "surface", 4.5],
    ["accent", "bg", 4.5],
    ["accent", "surface", 4.5],
    ["accent", "accent-soft", 4.5],
    ["accent-ink", "accent", 4.5],
    ["warn-ink", "warn-bg", 4.5],
    ["bad", "surface", 4.5],
    ["ink", "bad-bg", 4.5],
    ["input-line", "input-bg", 3],
    ["input-line", "surface", 3],
    ["accent", "sidebar", 3],
  ])("%s on %s reaches %s:1", (fg, bg, minimum) => {
    expect(contrast(fg as string, bg as string)).toBeGreaterThanOrEqual(minimum as number);
  });
});
