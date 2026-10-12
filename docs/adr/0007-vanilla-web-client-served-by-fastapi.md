# ADR 0007: Vanilla web client served by FastAPI

**Status:** accepted · 2026-10-12 · replaces ADR 0005 from 1.2.0

## Context

Streamlit came from the design report, which wanted the least possible frontend work. It demonstrates the flow, but it looks like a data notebook, runs as a second process on a second port, and pulls a large dependency tree into the image. The portfolio already has a pattern for small product UIs with no build step and no dependencies.

## Decision

- The client lives in `web/`: ES modules without a framework, a bundler or a `package.json`.
- Views are pure functions that return HTML strings. Every interpolated value goes through `h()`.
- `api.js` is the only module that calls `fetch`, and it names every endpoint in `ENDPOINTS`. A test checks each one against the OpenAPI schema.
- `format.js` prints the figures the API returns. The client never computes a metric; form inputs travel to the API as strings and the API validates them.
- FastAPI serves the client at `/ui/` from the same origin, so there is no CORS. Files are served by name from `WEB_FILES` in `app/api/routes/web.py`, with a strict CSP (`script-src 'self'; style-src 'self'`), `nosniff` and `no-referrer`. `/docs` keeps its own headers.
- `WEB_DIR` points to the folder. Without it the API runs alone.
- Client tests use `node:test` on the pure modules. CI runs them in the `web` job with Node 22.

## Consequences

- One process and one port for API and UI. The image no longer needs Streamlit once it is retired.
- The UI boundary from ADR 0005 still holds: the client only speaks HTTP, and replacing it touches no backend code.
- The repository gains a second language. Its checks are limited to syntax, pure-function tests and the contract test against OpenAPI; browser walkthroughs are recorded in pull requests.
- Streamlit runs next to the web client in 1.1.0 and is removed in 1.2.0.

## Alternatives rejected

- **React or another framework.** A build toolchain and a dependency tree for six screens.
- **Keeping Streamlit only.** Cheapest, and the weakest impression for the people this demo is for.
- **Serving the client from a separate static server.** Adds CORS and a second container for no gain at this size.
