# ADR 0016: Next.js at the root from 2.0.0

**Status:** accepted · 2026-10-19 · amends the migration and the rollback of ADR 0009

## Context

ADR 0009 moves from the vanilla client to Next.js in three phases. In phase 2, production serves `/app/` from Next.js beside `/ui/`, and in phase 3 (2.0.0) Next.js moves to `/`. It also has `deploy.sh` move both images to one tag and roll both back together.

On 2026-10-19 the Product Owner decided that the two clients never run side by side in public. During phase 2, a visitor would find two looks and two addresses for the same process, one of them a client still missing screens. The Product Owner also asked that the demo never break during the change.

The change itself touches three things on the server at once: the Nginx site, a new container and a new API image. Today `deploy.sh` knows one version (`APD_VERSION`), so a failed deploy of 2.0.0 could only go back to 1.x as a whole, with the Nginx site rolled back by hand while the demo is down.

## Decision

**No phase 2.** `/app/` never becomes public. Next.js keeps `basePath: '/app'` in development and CI until 2.0.0, while it reaches parity with `web/` (ADR 0015). `/ui/` stays the public client until then.

**Layout from 2.0.0.**

- Next.js serves the root `/`. `basePath: '/app'` goes, and the health check of the web image moves to `/`.
- FastAPI answers only under `/api/`. The root routes go, `/health` included, and `/api/health` is the one health endpoint.
- `/ui/` and every path under it answer 301 to `/`.
- Nginx sends `/api/` to FastAPI and every other path to Next.js. The analysis rate limit and the 200 second read timeout apply to `/api/processes/{id}/analyses`. `/_next/static/` gets its own burst and a long cache, because the first load of a Next.js page fetches many files at once.
- The routes live in one Nginx include shared by the host site and by an `edge` service in `compose.yaml`, so the end-to-end tests (RS-78) exercise the production routing.

**One version per service on the server.** The server `.env` records `APD_VERSION` for the API and `APD_WEB_VERSION` for the web image. Releases still publish both images with the same tag, and release-please writes both lines in `deploy/.env.example`. `deploy.sh` moves both services to the new tag. A 1.x tag moves the API only, because a 1.x web image still expects `/app`. When a health check fails (`/api/health` for the API, `/` for the web), it starts each service again on the version it ran before.

**The change on the server goes through states that always work.**

| State | Nginx | API | Web | Public client |
|---|---|---|---|---|
| S0 (today) | 1.x site | 1.x | not running | `/ui/` |
| S1 | 2.0.0 routing | 1.x, already under `/api/` | 2.0.0 | `/`, with `/ui/` answering 301 |
| S2 | 2.0.0 routing | 2.0.0 | 2.0.0 | `/` |

The repository variable `DEPLOY_ENABLED` stays off for the whole change, so a release cannot deploy halfway through it. The steps, which the runbook records with RS-79:

1. Install the new files and keep the current site as `apd.conf.1x`.
2. Start the web service alone and check it on its local port. Nothing public changes yet.
3. Switch the Nginx site, check it with `nginx -t` and the smoke test, and check that `/ui/` answers 301. This is S1.
4. Run `deploy.sh v2.0.0`. This is S2. If a health check fails, the script returns to S1, which also works.
5. Verify the demo, then switch `DEPLOY_ENABLED` back on.

## Consequences

- Visitors see `/ui/` until the release and the new client at `/` after it, never both. A bookmark of `/ui/` lands on the home page. Bookmarks with a hash route (`/ui/#/processes/<id>`) are an open decision.
- Every parity item has to merge before 2.0.0, so `/ui/` stays public longer than phase 2 would have kept it. The Product Owner accepts that in exchange for a demo that never looks half built.
- The server holds two version lines. They differ only during the change or after a partial rollback, and release-please keeps them equal in the repository.
- Everything that probes `/health` moves to `/api/health`: the API image health check, CI, `deploy.sh`, the smoke test and any external monitor.
- The root API URLs stop answering, which is why the change ships as 2.0.0. The fate of `/docs`, `/redoc` and `/openapi.json` at the root, which redirect to `/api/` today, is an open decision.
- A failed 2.0.0 deploy leaves the demo in S1 instead of taking it down.

## Alternatives rejected

| Option | Why not |
|---|---|
| Phase 2 of ADR 0009: `/app/` public beside `/ui/` | Two looks and two addresses for one process, and a client still missing screens in public |
| Keep Next.js at `/app/` after 2.0.0 | Longer addresses, and `/` would need a redirect for good |
| One version for both services on the server, as ADR 0009 has it | A rollback cannot express S1, so a failed 2.0.0 deploy goes back to S0 with the Nginx site restored by hand |
| Switch Nginx and both images in one step | No working state in between, so any failure takes the demo down until three things are rolled back |

## How to revert

- On the server: `deploy.sh v1.x` returns the API to 1.x and leaves the web service on 2.0.0, which is S1. Restoring `apd.conf.1x`, reloading Nginx and stopping the web service returns to S0.
- In the repository: restore `web/`, `web.py` and the root API routes from the last 1.x tag, and set `basePath: '/app'` again.
