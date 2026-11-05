import type { Page } from "@playwright/test";

import { expect, expectAccessible, test } from "./fixtures";

// RS-105: the full sidebar on Home, a rail of icons inside a process (ADR 0018). Runs at
// 1280 px and at 375 px like every walkthrough, where the navigation folds above the page.
const DEMO = "Order intake from distributors";
const LOAD_DEMO = new RegExp(`^Load and open ?: ${DEMO}$`);

/** The page is no wider than the screen: nothing scrolls sideways. */
async function expectNoSidewaysScroll(page: Page): Promise<void> {
  const overflow = await page.evaluate(
    () => document.documentElement.scrollWidth - document.documentElement.clientWidth,
  );
  expect(overflow, "horizontal overflow in px").toBeLessThanOrEqual(0);
}

test("RS-105.3: the navigation folds above the page with no horizontal scroll", async ({
  page,
}) => {
  await test.step("Home keeps the full sidebar", async () => {
    await page.goto("/");
    await expect(page.getByRole("link", { name: "New process" })).toBeVisible();
    await expect(page.getByRole("button", { name: "Processes" })).toHaveCount(0);
    await expectNoSidewaysScroll(page);
  });

  await test.step("a process page shows the rail", async () => {
    await page.getByRole("button", { name: LOAD_DEMO }).click();
    await expect(page.getByRole("heading", { name: DEMO, level: 1 })).toBeVisible();
    const rail = page.getByRole("list", { name: "Navigation" });
    await expect(rail.getByRole("link", { name: "Home" })).toBeVisible();
    await expect(rail.getByRole("link", { name: "New process" })).toBeVisible();
    await expectNoSidewaysScroll(page);
  });

  await test.step("the process list opens from the rail", async () => {
    await page.getByRole("button", { name: "Processes" }).click();
    const list = page.getByRole("navigation", { name: "Processes" });
    await expect(list.getByRole("link", { name: new RegExp(DEMO) }).first()).toBeVisible();
    const marks = await list
      .getByRole("link")
      .evaluateAll((links) => links.map((link) => link.getAttribute("aria-current")));
    expect(marks.filter((mark) => mark === "page")).toHaveLength(1);
    await expectNoSidewaysScroll(page);
    await expectAccessible(page, "the rail with the process list open");
    await page.keyboard.press("Escape");
    await expect(list).toBeHidden();
  });
});
