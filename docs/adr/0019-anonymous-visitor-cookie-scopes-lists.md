# ADR 0019: An anonymous visitor cookie scopes the process lists on the public demo

**Status:** accepted · 2026-11-03 · amends ADR 0008 (what the public demo shows)

## Context

The public demo has no accounts (PDR 001, ADR 0008). Every visitor sees every process in the list on Home and in the sidebar, and the banner warns that anything entered is visible to other visitors. PDR 004 adds an overview of how much this browser's processes consume, which needs to know which processes are this browser's. A total over the whole instance would add up strangers' data.

## Decision

- **Cookie.** On the public demo, the API gives each browser an anonymous id in a cookie named `apd_visitor`: a random UUID, with `HttpOnly; Secure; SameSite=Lax; Path=/api` and a `Max-Age` of 7 days. A request without a valid cookie gets a new one. The cookie carries nothing else.
- **Storage.** `processes` gains a nullable, indexed `visitor_id` column, added by an Alembic migration. Every path that creates a process records the visitor: a new process, a demo loaded, a process started from a template, and later an AI draft.
- **Lists only.** `GET /processes` and the portfolio overview return the visitor's processes only. Reading, editing and analysing a process by its id do not change, so a shared link keeps working.
- **The cookie is no credential.** It scopes lists and grants nothing. Knowing a process id is enough to open it, as today, and the banner says that anything entered is visible to anyone with its link.
- **Public demo only.** With `public_demo=false` (a local install, the tests, API clients), the API sets no cookie and lists every process, as before.
- **Never in a body.** No response body includes the visitor id, so the gzip compression of `deploy/nginx/apd.conf` still has no secret to leak in a BREACH-style attack. The comment there is updated with RS-110, since a cookie now travels in a header.
- **Layers.** `api/dependencies.py` reads or issues the cookie and passes a plain `UUID | None` to the services, which import no FastAPI (hard rule 1 and `tests/unit/test_boundaries.py`).
- **Consent.** The cookie is strictly necessary for a function the visitor uses and holds no tracking, so it needs no consent banner. The demo stores no other cookie besides the `theme` preference of ADR 0013.

## Consequences

- A demo visitor stops seeing other visitors' processes in the lists. Processes created before the migration have no visitor, show in no list on the demo, and leave with the 24-hour purge.
- A visitor who clears cookies, or opens the demo in another browser, loses the list of their processes. The processes still exist until the purge and still open from their links.
- One more migration and a column to keep in mind in the purge and in the restore runbook.
- The e2e walkthroughs need two browser contexts to prove the scoping.

## Alternatives rejected

| Alternative | Why not |
|---|---|
| Process ids kept in `localStorage` and sent with each list request | Lost when site data is cleared, can throw in private windows, and every list request would need the ids in its body; the sidebar and Home would depend on client state for a server fact |
| A 404 for processes of other visitors | Makes the cookie a credential without the protection of one, touches every route, and breaks shared links, which are part of how the demo is shown |
| Accounts or sign-in | Out of scope for the demo (PDR 001); a visitor must try it without signing up (RU-09) |
| Scope on every install, not only the public demo | A local install has one user, and API clients and tests without a cookie would see an empty list |
