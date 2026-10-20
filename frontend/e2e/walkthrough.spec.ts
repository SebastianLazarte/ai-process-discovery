import { readFile } from "node:fs/promises";

import { expect, expectAccessible, test } from "./fixtures";

// RS-78: the critical path of the demo, through the production routes with the fake LLM
// provider. Load a demo, run an analysis, save an override and download the blueprint,
// with axe on every page on the way (ADR 0013). The client lives at the root (ADR 0016).
const HOME = "/";
const DEMO = "Order intake from distributors";
// The demo name follows a visually hidden ": ", read with a space before the colon.
const LOAD_DEMO = new RegExp(`^Load and open ?: ${DEMO}$`);
const ANALYSIS_URL = /\/processes\/([^/]+)\/analyses\/([^/]+)$/;
const REASON = "The order desk keeps the final check.";

test("load a demo, analyse, override and download the blueprint", async ({ page }) => {
  await test.step("home", async () => {
    await page.goto(HOME);
    await expect(page.getByRole("heading", { name: "Start from a demo" })).toBeVisible();
    await expect(page.getByRole("button", { name: LOAD_DEMO })).toBeEnabled();
    await expectAccessible(page, "home");
  });

  const demoAnalysis = await test.step("load a demo", async () => {
    await page.getByRole("button", { name: LOAD_DEMO }).click();
    // A demo with assumptions comes with its first analysis, and opens its results.
    await page.waitForURL(ANALYSIS_URL);
    await expect(page.getByRole("heading", { name: DEMO, level: 1 })).toBeVisible();
    await expect(page.getByRole("heading", { name: "Step by step", exact: true })).toBeVisible();
    await expectAccessible(page, "results of the demo");
    return page.url().match(ANALYSIS_URL)?.[2];
  });

  const tabs = page.getByRole("navigation", { name: "Process sections" });

  const analysisId = await test.step("run an analysis", async () => {
    await tabs.getByRole("link", { name: "Analyse" }).click();
    await expect(page.getByRole("heading", { name: "Analyse", exact: true })).toBeVisible();
    await page.getByLabel("Implementation cost").fill("12000");
    // The first step's slider, moved with the keyboard: ten steps of 5 %.
    const slider = page.getByRole("slider").first();
    for (let i = 0; i < 10; i++) await slider.press("ArrowRight");
    await expect(slider).toHaveValue("0.5");
    await page.getByLabel(/Enrich with the LLM/).check();
    // The demo has a step with sensitive data: its description needs consent to leave.
    await page.getByLabel("I confirm these descriptions can be sent to the provider").check();
    await expectAccessible(page, "analyse");

    await page.getByRole("button", { name: "Run analysis" }).click();
    await expect(page.getByText("Analysis saved.")).toBeVisible();
    await expect(page).not.toHaveURL(new RegExp(`/analyses/${demoAnalysis}$`));
    await page.waitForURL(ANALYSIS_URL);
    await expect(page.getByRole("heading", { name: "Step by step", exact: true })).toBeVisible();
    const id = page.url().match(ANALYSIS_URL)?.[2];
    expect(id).toBeTruthy();
    return id as string;
  });

  await test.step("results", async () => {
    await expectAccessible(page, "results of the new analysis");
  });

  await test.step("save an override", async () => {
    const step = page.locator("details").first();
    await step.locator("summary").click();
    const form = step.getByRole("region", { name: /^Override / });
    await form.getByLabel("Method").selectOption("MANUAL");
    await form.getByLabel("Human control").selectOption("REQUIRED");
    await form.getByLabel("Reason").fill(REASON);
    await form.getByRole("button", { name: "Save override" }).click();
    await expect(page.getByText("Override saved.", { exact: false })).toBeVisible();
    await expect(step.getByRole("region", { name: "Override", exact: true })).toContainText(REASON);
    await expectAccessible(page, "results with an override");

    // The API keeps it: the step's decision is the override, with its reason.
    const saved = await page.request.get(`/api/analyses/${analysisId}`);
    expect(saved.ok()).toBe(true);
    const first = (await saved.json()).step_assessments[0];
    expect(first.final_method).toBe("MANUAL");
    expect(first.final_human_control).toBe("REQUIRED");
    expect(first.override.reason).toBe(REASON);
  });

  await test.step("download the blueprint", async () => {
    await tabs.getByRole("link", { name: "Blueprint" }).click();
    const link = page.getByRole("link", { name: "Download .md" });
    await expect(link).toBeVisible();
    await expect(page.getByRole("heading", { name: "8. Workflow specification" })).toBeVisible();
    await expectAccessible(page, "blueprint");

    const [download] = await Promise.all([page.waitForEvent("download"), link.click()]);
    const file = await readFile(await download.path());
    const api = await page.request.get(`/api/analyses/${analysisId}/blueprint.md`);
    expect(api.ok()).toBe(true);
    // The browser saved the API's own bytes, with the override applied.
    expect(file.equals(await api.body())).toBe(true);
    expect(file.toString("utf8")).toContain(REASON);
  });
});
