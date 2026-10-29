import { expect, expectAccessible, test } from "./fixtures";

// RS-96: start a process from a sector template through the production routes. Pick the
// sector and the process, type only the figures of the company, and the new process opens
// on its Steps page with the template's steps, with axe on every page on the way.
const SECTOR = "Manufacturing";
const TEMPLATE = "Supplier invoice processing";
const STEPS_URL = /\/processes\/[^/]+$/;

test("RS-96: start a process from a sector template", async ({ page }) => {
  await test.step("choose a template", async () => {
    await page.goto("/processes/new");
    await page.getByLabel("Sector").selectOption({ label: SECTOR });
    await page.getByLabel("Process", { exact: true }).selectOption({ label: TEMPLATE });
    await expect(page.getByRole("heading", { name: `Review: ${TEMPLATE}` })).toBeVisible();
    await expectAccessible(page, "template review");
  });

  const review = page.getByRole("region", { name: `Review: ${TEMPLATE}` });
  const minutes = review.getByLabel("Minutes per execution");
  const count = await minutes.count();

  await test.step("missing figures stay on the review", async () => {
    await review.getByRole("button", { name: "Create process" }).click();
    await expect(review.getByText("Enter the executions per month.")).toBeVisible();
    await expect(page).toHaveURL(/\/processes\/new$/);
    await expectAccessible(page, "template review with errors");
  });

  await test.step("create the process", async () => {
    await review.getByLabel("Executions per month").fill("400");
    for (let i = 0; i < count; i++) await minutes.nth(i).fill("5");
    await review.getByRole("button", { name: "Create process" }).click();
    await page.waitForURL(STEPS_URL);
    await expect(page.getByRole("heading", { name: TEMPLATE, level: 1 })).toBeVisible();
    await expect(page.getByRole("heading", { name: "Steps", exact: true })).toBeVisible();
    await expectAccessible(page, "steps of the new process");
  });

  await test.step("the API keeps every step of the template", async () => {
    const id = page.url().match(STEPS_URL)?.[0].split("/").pop();
    const saved = await page.request.get(`/api/processes/${id}`);
    expect(saved.ok()).toBe(true);
    const process = await saved.json();
    expect(process.executions_per_month).toBe(400);
    expect(process.steps).toHaveLength(count);
    expect(Number(process.steps[0].minutes_per_execution)).toBe(5);
  });
});
