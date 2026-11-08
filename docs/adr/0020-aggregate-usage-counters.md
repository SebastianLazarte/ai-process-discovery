# ADR 0020: Aggregate daily usage counters on the public demo

**Status:** accepted · 2026-11-07 · amends ADR 0008 (what the demo keeps after the purge)

## Context

The live demo is the Product Goal (PDR 002), yet the maintainer cannot tell whether anyone uses it. The purge deletes every process after 24 hours (ADR 0008, RS-63), the container logs rotate after 30 MB, and the Nginx access log says which paths were called but not whether a visitor loaded a demo or described their own process. There is no analytics tool, and the banner promises that visitor data is deleted daily.

## Decision

- **Counters, not events.** A table `usage_counters` holds one row per UTC day and event: `day`, `event` and `count`, with `(day, event)` as primary key. A counted request adds one to its row with an upsert (`INSERT ... ON CONFLICT DO UPDATE` on both engines), so concurrent requests never lose a count. An Alembic migration adds the table.
- **Six events.** `process_created` (`POST /processes`, which also covers a process started from a template), `demo_loaded` (`POST /demo-processes/{slug}`), `analysis_run`, `override_created`, `blueprint_viewed` (`GET .../blueprint`) and `blueprint_downloaded` (`GET .../blueprint.md`). A request is counted only after it succeeds.
- **Counted at the route.** The API route records the event after its service returns, through a `UsageService` that imports no FastAPI. The route is where a visitor's intent is known: loading a demo creates a process and runs an analysis inside `DemoService`, and those must not count as the visitor's own.
- **Never in the way.** A counter that cannot be written is rolled back and logged as `usage_not_recorded`; the request still succeeds.
- **Nothing personal.** A row holds no process id, text, IP address, user agent or visitor id (ADR 0019). Counts by day cannot be traced back to a visitor, so they are kept after the purge and need no consent banner. `SECURITY.md` says so next to the data policy.
- **Read on the server only.** `python -m app.usage --days N` prints one row per UTC day, newest first, with a column per event and a total row. No HTTP route exposes the counters, so the demo needs no operator credential.

## Consequences

- The maintainer sees each day how many visitors describe their own process, try a demo, run an analysis or reach the blueprint, and where they stop, for as long as the database lives.
- The counters cannot tell unique visitors apart. A visitor who loads three demos counts three times.
- One more table, migration and write per counted request; one more command in the runbook.
- Counts from tests, local runs and the e2e walkthroughs stay in their own databases and never reach the demo.

## Alternatives rejected

| Alternative | Why not |
|---|---|
| Self-hosted Umami or Plausible | A new service, database and client script, a wider Content Security Policy and more data about visitors than the question needs |
| A hosted analytics service | Sends visitor data to a third party and needs a consent banner |
| Keeping processes longer | Breaks the promise of the banner and keeps what visitors typed |
| Counting from the Nginx access log | Rotated, holds IP addresses, and cannot tell a demo's analysis from a visitor's own |
| An event table with timestamps and ids | More than the question needs, and ids would tie rows to visitors |
| A `GET /usage` route with an operator token | A secret to manage and more surface on a public host for numbers the maintainer reads over SSH anyway |
