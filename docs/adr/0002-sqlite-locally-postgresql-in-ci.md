# ADR 0002: SQLite locally, PostgreSQL verified in CI, no migrations yet

**Status:** accepted · 2026-10-07

## Context

The design report recommends PostgreSQL from the start. The development machine has neither Docker nor PostgreSQL. The demo has one writer at a time.

## Decision

- The database is chosen with `DATABASE_URL`. SQLite is the default for local runs.
- The `test-postgres` CI job runs the whole integration suite against PostgreSQL 17 on every pull request, and `compose.yaml` runs the stack on PostgreSQL. The PostgreSQL path is therefore tested continuously, not assumed.
- Exact decimals on both engines through `ExactDecimal`: native `NUMERIC` on PostgreSQL, text on SQLite, never float.
- Tables are created with `create_all`. There are no Alembic migrations while no schema version has been released.

## Consequences

- Running the demo needs nothing beyond `uv`.
- A schema change before 1.0 means recreating the local database.

## How to revert

- To make PostgreSQL the local default: change `DATABASE_URL` in `.env`.
- To add migrations: add Alembic, generate the initial migration from the current models, replace `init_db` with `alembic upgrade head`. Do this before the first release that users keep data in.
