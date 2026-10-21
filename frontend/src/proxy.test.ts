// @vitest-environment node
import { unstable_doesMiddlewareMatch } from "next/experimental/testing/server";
import { NextRequest } from "next/server";
import { afterEach, describe, expect, it, vi } from "vitest";

import nextConfig from "../next.config";
import { config, NONCE_HEADER, proxy } from "./proxy";

function request(path = "/") {
  return new NextRequest(new URL(path, "http://localhost:3000"));
}

function directives(csp: string): Map<string, string[]> {
  return new Map(
    csp.split(";").map((directive) => {
      const [name = "", ...sources] = directive.trim().split(/\s+/);
      return [name, sources];
    }),
  );
}

function nonceOf(csp: string): string {
  const nonce = /'nonce-([^']+)'/.exec(directives(csp).get("script-src")!.join(" "))?.[1];
  expect(nonce).toBeDefined();
  return nonce!;
}

afterEach(() => {
  vi.unstubAllEnvs();
});

describe("proxy (RS-72)", () => {
  it("answers a page with a nonce CSP, nosniff, no-referrer and frame-ancestors 'none'", () => {
    const response = proxy(request("/processes/abc"));

    const csp = response.headers.get("Content-Security-Policy")!;
    expect(nonceOf(csp)).toMatch(/^[A-Za-z0-9+/]{22}==$/);
    expect(directives(csp).get("frame-ancestors")).toEqual(["'none'"]);
    expect(response.headers.get("X-Content-Type-Options")).toBe("nosniff");
    expect(response.headers.get("Referrer-Policy")).toBe("no-referrer");
  });

  it("keeps unsafe-inline out of script-src, and unsafe-eval out of production", () => {
    vi.stubEnv("NODE_ENV", "production");

    const scriptSrc = directives(proxy(request()).headers.get("Content-Security-Policy")!).get(
      "script-src",
    );

    expect(scriptSrc).not.toContain("'unsafe-inline'");
    expect(scriptSrc).not.toContain("'unsafe-eval'");
    expect(scriptSrc).toContain("'strict-dynamic'");
  });

  it("relaxes eval and inline styles in development only, never inline scripts", () => {
    vi.stubEnv("NODE_ENV", "development");

    const csp = directives(proxy(request()).headers.get("Content-Security-Policy")!);

    expect(csp.get("script-src")).toContain("'unsafe-eval'");
    expect(csp.get("script-src")).not.toContain("'unsafe-inline'");
    expect(csp.get("style-src")).toEqual(["'self'", "'unsafe-inline'"]);
  });

  it("blocks inline styles that carry no nonce", () => {
    vi.stubEnv("NODE_ENV", "production");

    const csp = proxy(request()).headers.get("Content-Security-Policy")!;

    expect(directives(csp).get("style-src")).toEqual(["'self'", `'nonce-${nonceOf(csp)}'`]);
  });

  it("hands the same nonce to the render through the request headers", () => {
    const response = proxy(request());
    const csp = response.headers.get("Content-Security-Policy")!;

    // NextResponse.next() carries the rewritten request headers in x-middleware-request-*.
    expect(response.headers.get(`x-middleware-request-${NONCE_HEADER}`)).toBe(nonceOf(csp));
    expect(response.headers.get("x-middleware-request-content-security-policy")).toBe(csp);
  });

  it("draws a fresh nonce for every request", () => {
    const nonces = new Set(
      Array.from({ length: 20 }, () =>
        nonceOf(proxy(request()).headers.get("Content-Security-Policy")!),
      ),
    );

    expect(nonces.size).toBe(20);
  });
});

describe("proxy matcher", () => {
  const matches = (url: string, headers?: Record<string, string>) =>
    unstable_doesMiddlewareMatch({ config, nextConfig, url, headers });

  it.each(["/", "/processes/abc", "/processes/abc/analyses/def"])("runs on the page %s", (url) => {
    expect(matches(url)).toBe(true);
  });

  it.each(["/_next/static/chunks/main.js", "/_next/image", "/favicon.ico"])(
    "skips the static file %s",
    (url) => {
      expect(matches(url)).toBe(false);
    },
  );

  it("skips a link prefetch", () => {
    expect(matches("/processes/abc", { "next-router-prefetch": "1" })).toBe(false);
  });
});
