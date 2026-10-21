import { expect, test } from "./fixtures";

// RS-80: the vanilla client and the root API routes are gone in 2.0.0 (ADR 0016). Old
// bookmarks under /ui/ answer 301 to the home page, which Next.js serves, and the API only
// answers under /api/.
//
// Plain requests, no page: a full page load pulls every static file through the edge's
// per-address rate limit, which the walkthroughs share. The viewport changes nothing here,
// so the mobile project skips the file.
const OLD_LINKS = ["/ui", "/ui/", "/ui/app.js", "/ui/index.html"];

test.skip(({ isMobile }) => isMobile, "Routing does not depend on the viewport");

for (const path of OLD_LINKS) {
  test(`${path} answers 301 to the home page`, async ({ request }) => {
    const response = await request.get(path, { maxRedirects: 0 });

    expect(response.status()).toBe(301);
    expect(new URL(response.headers()["location"] ?? "", "http://edge").pathname).toBe("/");
  });
}

test("an old /ui/ bookmark lands on the home page of the new client", async ({ request }) => {
  // The fragment of a 1.x link (#/processes/...) never reaches the server.
  const response = await request.get("/ui/");

  expect(response.status()).toBe(200);
  expect(new URL(response.url()).pathname).toBe("/");
  expect(await response.text()).toContain("<title>AI Process Discovery</title>");
});

test("the API answers under /api/ only", async ({ request }) => {
  expect((await request.get("/api/processes")).status()).toBe(200);
  expect((await request.get("/api/health")).status()).toBe(200);
  // Next.js owns every other path: the old root route is one of its pages now, not JSON.
  const root = await request.get("/processes");
  expect(root.headers()["content-type"]).not.toContain("application/json");
});
