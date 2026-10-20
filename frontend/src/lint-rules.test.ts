// @vitest-environment node
// RS-70: lint enforces hard rule 7. Each test lints a snippet as if it lived at a given path.
import { ESLint } from "eslint";
import { beforeAll, describe, expect, it } from "vitest";

const eslint = new ESLint();

// The first lint loads the Next presets and the TypeScript parser, which takes seconds on a
// cold start, and far longer on a busy machine. Paying it once here keeps each test within
// the default timeout.
beforeAll(() => eslint.lintText("", { filePath: "src/warm-up.ts" }), 180_000);

async function ruleIds(code: string, filePath: string): Promise<string[]> {
  const [result] = await eslint.lintText(code, { filePath });
  return (result?.messages ?? []).filter((m) => m.severity === 2).map((m) => m.ruleId ?? "parse");
}

describe("fetch outside src/lib/api/", () => {
  const call = `export async function load() {
  return fetch("/api/processes");
}
`;

  it("fails in a component", async () => {
    expect(await ruleIds(call, "src/components/process-list.tsx")).toContain(
      "no-restricted-globals",
    );
  });

  it("fails through window or globalThis", async () => {
    const indirect = `export const load = () => [window.fetch("/a"), globalThis.fetch("/b")];\n`;
    expect(await ruleIds(indirect, "src/components/process-list.tsx")).toEqual([
      "no-restricted-properties",
      "no-restricted-properties",
    ]);
  });

  it("passes in src/lib/api/", async () => {
    expect(await ruleIds(call, "src/lib/api/client.ts")).toEqual([]);
  });
});

describe("dangerouslySetInnerHTML", () => {
  const component = `export function Note({ html }: { html: string }) {
  return <div dangerouslySetInnerHTML={{ __html: html }} />;
}
`;

  it("fails as a JSX attribute", async () => {
    expect(await ruleIds(component, "src/components/note.tsx")).toContain("react/no-danger");
  });

  it("fails when built as a props object", async () => {
    const spread = `export function Note({ html }: { html: string }) {
  const props = { dangerouslySetInnerHTML: { __html: html } };
  return <div {...props} />;
}
`;
    expect(await ruleIds(spread, "src/components/note.tsx")).toContain("no-restricted-syntax");
  });

  it("fails even inside src/lib/api/", async () => {
    expect(await ruleIds(component, "src/lib/api/note.tsx")).toContain("react/no-danger");
  });
});

describe("the style prop", () => {
  it("fails on any element, because the CSP blocks inline styles", async () => {
    const styled = `export function Bar({ width }: { width: number }) {
  return <div style={{ width: \`\${width}%\` }} />;
}
`;
    expect(await ruleIds(styled, "src/components/bar.tsx")).toContain("no-restricted-syntax");
  });

  it("leaves a className alone", async () => {
    const classed = `export function Bar() {
  return <div className="w-full" />;
}
`;
    expect(await ruleIds(classed, "src/components/bar.tsx")).toEqual([]);
  });
});
