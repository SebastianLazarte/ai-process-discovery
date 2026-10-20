import { expect, test } from "./fixtures";

// RS-80: the vanilla client and the root API routes are gone in 2.0.0 (ADR 0016). Old
// bookmarks under /ui/ answer 301 to the home page, which Next.js serves, and the API only
// answers under /api/.
const OLD_LINKS = ["/ui", "/ui/", "/ui/app.js", "/ui/index.html"];

for (const path of OLD_LINKS) {
  test(`${path} answers 301 to the home page`, async ({ request }) => {
    const response = await request.get(path, { maxRedirects: 0 });

    expect(response.status()).toBe(301);
    expect(new URL(response.headers()["location"] ?? "", "http://edge").pathname).toBe("/");
  });
}

test("an old /ui/ bookmark opens the home page of the new client", async ({ page }) => {
  // The fragment of a 1.x link (#/processes/...) never reaches the server, and the browser
  // keeps it across the redirect, where the new client ignores it.
  await page.goto("/ui/#/processes/abc");

  expect(new URL(page.url()).pathname).toBe("/");
  await expect(page.getByRole("heading", { name: "Start from a demo" })).toBeVisible();
});

test("the API answers under /api/ only", async ({ request }) => {
  expect((await request.get("/api/processes")).status()).toBe(200);
  expect((await request.get("/api/health")).status()).toBe(200);
  // Next.js owns every other path: the old root route is one of its pages now, not JSON.
  const root = await request.get("/processes");
  expect(root.headers()["content-type"]).not.toContain("application/json");
});
