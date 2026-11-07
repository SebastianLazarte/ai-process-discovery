import { defineConfig, devices } from "@playwright/test";

// RS-78: the walkthroughs run against the compose stack through its edge Nginx on :8080,
// which serves the production routes (deploy/nginx/apd-routes.conf), with the fake LLM
// provider. ADR 0013: every walkthrough runs at 1280 px and at 375 px.
export default defineConfig({
  testDir: "e2e",
  forbidOnly: !!process.env.CI,
  // One browser at a time: both projects reach the edge from the same address. Each test
  // gets its own rate limit bucket there (X-E2E-Visitor, set in e2e/fixtures.ts).
  workers: 1,
  reporter: process.env.CI ? [["github"], ["html", { open: "never" }]] : [["list"]],
  use: {
    baseURL: process.env.E2E_BASE_URL ?? "http://localhost:8080",
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
  },
  projects: [
    {
      name: "desktop",
      use: { ...devices["Desktop Chrome"], viewport: { width: 1280, height: 800 } },
    },
    {
      name: "mobile",
      use: {
        ...devices["Desktop Chrome"],
        viewport: { width: 375, height: 812 },
        deviceScaleFactor: 2,
        isMobile: true,
        hasTouch: true,
      },
    },
  ],
});
