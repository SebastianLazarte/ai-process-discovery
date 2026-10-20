import { NextResponse, type NextRequest } from "next/server";

// ADR 0009 and RS-72: every page carries a strict CSP with a fresh nonce, as strict as the
// one FastAPI sends for /ui/. Next reads the nonce back from the request's CSP header and
// stamps it on its own scripts, so a page only renders with it when rendered per request
// (the root layout opts every page into dynamic rendering).

/** The request header that hands the nonce to server components. */
export const NONCE_HEADER = "x-nonce";

/** 128 random bits, base64: fresh for every request and unguessable. */
export function createNonce(): string {
  const bytes = crypto.getRandomValues(new Uint8Array(16));
  return btoa(String.fromCharCode(...bytes));
}

/**
 * `'strict-dynamic'` lets the nonced Next runtime load its own chunks. Styles come from
 * same-origin files only, so an inline `style=` attribute is blocked: shapes such as a
 * bar's width go through native elements (`<meter>`, `<progress>`) instead.
 *
 * Development relaxes two sources that production never sends: React needs `eval` for its
 * error stacks, and the Next dev tools (the error overlay) inject `<style>` tags without a
 * nonce. A nonce would switch `'unsafe-inline'` off, so development leaves it out of
 * `style-src`.
 */
export function contentSecurityPolicy(nonce: string, isDev: boolean): string {
  return [
    "default-src 'self'",
    `script-src 'self' 'nonce-${nonce}' 'strict-dynamic'${isDev ? " 'unsafe-eval'" : ""}`,
    isDev ? "style-src 'self' 'unsafe-inline'" : `style-src 'self' 'nonce-${nonce}'`,
    "img-src 'self' data:",
    "font-src 'self'",
    "connect-src 'self'",
    "object-src 'none'",
    "frame-ancestors 'none'",
    "base-uri 'none'",
    "form-action 'self'",
  ].join("; ");
}

export function proxy(request: NextRequest): NextResponse {
  const nonce = createNonce();
  const csp = contentSecurityPolicy(nonce, process.env.NODE_ENV === "development");

  const requestHeaders = new Headers(request.headers);
  requestHeaders.set(NONCE_HEADER, nonce);
  requestHeaders.set("Content-Security-Policy", csp);

  const response = NextResponse.next({ request: { headers: requestHeaders } });
  response.headers.set("Content-Security-Policy", csp);
  response.headers.set("X-Content-Type-Options", "nosniff");
  response.headers.set("Referrer-Policy", "no-referrer");
  return response;
}

// Every page, after the basePath that Next prefixes. Hashed static files and optimised
// images run no script of their own, and a prefetch only fetches data for a page that
// already carries the policy. "/" stands for the bare basePath (/app), which the
// catch-all source alone does not match. Next reads this object at build time, so it
// stays literal.
export const config = {
  matcher: [
    {
      source: "/",
      missing: [
        { type: "header", key: "next-router-prefetch" },
        { type: "header", key: "purpose", value: "prefetch" },
      ],
    },
    {
      source: "/((?!_next/static|_next/image|favicon.ico).*)",
      missing: [
        { type: "header", key: "next-router-prefetch" },
        { type: "header", key: "purpose", value: "prefetch" },
      ],
    },
  ],
};
