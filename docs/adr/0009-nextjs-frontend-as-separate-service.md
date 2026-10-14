# ADR 0009: Next.js frontend as a separate service

**Status:** accepted · 2026-10-14 · replaces ADR 0007 from 2.0.0; amends the required checks of ADR 0006 and the layout of ADR 0008

## Context

ADR 0007 replaced Streamlit with a vanilla client: ES modules, no build step, no dependencies, served by FastAPI at `/ui/`. It works and keeps one process, but the portfolio also has to show frontend engineering with a current toolchain: typed components, generated API types, component and end-to-end tests, a build pipeline and an image of its own. ADR 0007 rejected React because six screens did not justify a toolchain. The toolchain is now part of what the demo is meant to show, so that reason no longer holds.

The principles stay: Python computes every number (ADR 0001), the client only speaks HTTP (ADR 0005), and the public demo keeps running during the change (ADR 0008).

## Decision

**Service.** The client is a Next.js application (App Router, TypeScript strict) in `frontend/`, built with `output: 'standalone'` and run as a second container. pnpm manages it, and Node 22 is pinned in `.nvmrc`, `engines` and `packageManager`.

**Routing.** Nginx routes by path on one origin, so there is no CORS. `/api/` goes to FastAPI and everything else goes to Next. The rate limit on analysis runs and the long LLM read timeout stay in Nginx. In development, `next dev` rewrites `/api/` to `localhost:8000`.

**URLs.** The API moves under `/api` (`/api/docs`, `/api/openapi.json`). Next owns `/`.

**Client rules.** These carry over from ADR 0007 and hard rule 7:

- The client never computes a metric. It prints the figures the API returns, and one module (`src/lib/format`) turns them into text.
- Only `src/lib/api/` calls `fetch`. Its types are generated from the committed `openapi.json` with `openapi-typescript`, and requests go through `openapi-fetch`. A pytest check fails when `openapi.json` differs from `app.openapi()`, and the `frontend` job fails when the generated types differ from the committed ones. This replaces the `ENDPOINTS` check.
- React escapes interpolated values, which replaces `h()`. Lint forbids `dangerouslySetInnerHTML` and any `fetch` outside `src/lib/api/`.
- Reads may be prefetched in Server Components through the same client with an internal base URL (`API_INTERNAL_URL`). Mutations always leave from the browser, so they pass through Nginx and its rate limits.
- Option lists match the domain enums from `/api/meta`.

**Security headers.** Next sets them on every response: a CSP with a per-request nonce (no `unsafe-inline` in `script-src`), `nosniff`, `no-referrer` and `frame-ancestors 'none'`.

**Dependencies.**

| Package | Why |
|---|---|
| `next`, `react`, `react-dom` | Framework and rendering |
| `typescript` | Strict types across the client |
| `tailwindcss` | Styling without hand-written CSS files |
| shadcn/ui (Radix primitives, copied into the repo) | Accessible components that the repo owns |
| `@tanstack/react-query` | Server state, caching and loading states |
| `openapi-typescript`, `openapi-fetch` | API types generated from the backend contract |
| `react-hook-form`, `zod` | Forms and client-side input shape; the API still validates every value |
| `vitest`, `@testing-library/react` | Unit and component tests |
| `@playwright/test` | End-to-end tests against the compose stack |
| `eslint`, `prettier` | Lint, including the client rules above, and formatting |

**Tests and checks.** Two required checks are added: `frontend` (lint, typecheck, unit and component tests, generated types up to date, build) and `e2e` (Playwright against the compose stack with `FakeLLMProvider`). The `e2e` walkthroughs replace the manual browser walkthroughs recorded in pull requests. The `web` check leaves with the vanilla client.

**Images and releases.** The release workflow publishes `ai-process-discovery` and `ai-process-discovery-web` with the same `X.Y.Z` tag, both with SBOM and provenance. release-please keeps one version for the repository. `deploy.sh` moves both images to the same tag, and a rollback moves both back.

**Migration.** The two clients run side by side, as Streamlit and the web client did:

1. The API answers under `/api` and at the root. Next runs with `basePath: '/app'` and reaches parity screen by screen, with the vanilla client still at `/ui/`.
2. Production serves `/app/` from Next and `/api/` from FastAPI, behind the same Nginx site. Every other path still goes to FastAPI.
3. Version 2.0.0 removes `web/`, the root API routes and the `web` check. Next moves to `/`, and `/ui/` redirects there.

The requirements are RS-69 to RS-80 in `docs/requirements.toml` (block B12).

## Consequences

- Two processes, two images and two health checks. The VPS has room for them (ADR 0008), and the Next container gets its own memory and CPU limits.
- The repository gains a Node toolchain with a lockfile. Dependabot covers it, and CodeQL adds `javascript-typescript`.
- A per-request nonce makes every page dynamically rendered. For an application that shows per-process data, the cost is small.
- Moving the API under `/api` breaks any client that calls the root routes, so the retirement ships as 2.0.0.
- The UI boundary from ADR 0005 still holds: the frontend only speaks HTTP, and the backend keeps no knowledge of it once `web.py` is gone.

## Alternatives rejected

| Option | Why not |
|---|---|
| Static export served by FastAPI | Keeps one process, but the App Router emits inline scripts that break `script-src 'self'`, and the demo would show no server rendering |
| Next proxies the API through rewrites | The rate limit leaves Nginx, and the proxy timeout has to cover LLM runs of up to 200 seconds |
| Next as a backend for frontend only | Per-IP rate limiting gets harder and `/docs` stops being public |
| Keeping the vanilla client | Cheapest, and it shows no frontend toolchain |
| Separate versions for API and frontend | Needs a compatibility matrix and makes rollback harder, for a single maintainer |

## How to revert

Restore `web/` and `web.py` from the last 1.x tag, remove the `web` service from both compose files and the Next location from the Nginx site, and keep the `/api` prefix, which the vanilla client can call through `ENDPOINTS`.
