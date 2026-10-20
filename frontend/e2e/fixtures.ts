import AxeBuilder from "@axe-core/playwright";
import { test as base, expect } from "@playwright/test";
import type { Page } from "@playwright/test";

// The WCAG 2.2 AA target of ADR 0013.
const WCAG_TAGS = ["wcag2a", "wcag2aa", "wcag21a", "wcag21aa", "wcag22aa"];
const BLOCKING = new Set(["serious", "critical"]);

// Chrome logs every blocked load, script or inline style with this phrase.
const CSP = /Content Security Policy/i;

/**
 * Fails a test on a CSP violation (RS-72) or an uncaught error in the page, whichever page
 * of the walkthrough it happened on. The parameter is not named `use`, which the React hooks
 * lint rule would take for the hook of that name.
 */
export const test = base.extend<{ pageProblems: void }>({
  pageProblems: [
    async ({ page }, run) => {
      const problems: string[] = [];
      page.on("console", (message) => {
        if (message.type() === "error" && CSP.test(message.text())) problems.push(message.text());
      });
      page.on("pageerror", (error) => problems.push(`Uncaught: ${error.message}`));
      await run();
      expect(problems, "CSP violations or uncaught errors in the page").toEqual([]);
    },
    { auto: true },
  ],
});

export { expect };

/** Runs axe on the page as it stands and fails on any serious or critical violation. */
export async function expectAccessible(page: Page, name: string): Promise<void> {
  const results = await new AxeBuilder({ page }).withTags(WCAG_TAGS).analyze();
  const blocking = results.violations.filter((v) => v.impact && BLOCKING.has(v.impact));
  const report = blocking
    .map((v) => `${v.id} (${v.impact}): ${v.help}\n  ${v.nodes.map((n) => n.target).join("\n  ")}`)
    .join("\n");
  expect(report, `serious or critical axe violations on ${name}`).toBe("");
}
