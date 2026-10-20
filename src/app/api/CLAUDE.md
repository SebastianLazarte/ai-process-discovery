# API

Thin FastAPI routes: validate the contract, call a service, return a schema. Business decisions live in `services/` and `domain/`.

## Read

- `docs/adr/0003-separate-domain-contracts-persistence.md`
- `docs/adr/0016-nextjs-at-the-root-from-2-0-0.md`: the API answers under `/api` only

## Rules

- Services come in through `dependencies.py`.
- Errors are `AppError` subclasses from `core/errors.py`; `main.py` turns them into `{"detail", "code"}` responses. Domain validation errors become 422.
- Analysing a step flagged as sensitive needs `confirm_sensitive=true`; without it the service raises a 409.
- Routers are mounted under `/api` only (ADR 0009, ADR 0016, RS-80): the root belongs to the Next.js client, which Nginx serves. The schema documents each path once, relative to its `servers` entry `/api`. Docs live at `/api/docs`, and `/docs`, `/redoc` and `/openapi.json` answer 301 there. The API serves no client files.
- `frontend/openapi.json` is the contract the Next.js client generates its types from. After changing a route or a schema, run `uv run python scripts/export_openapi.py`, then `corepack pnpm api:types` in `frontend/`. `tests/unit/test_openapi_contract.py` fails until the contract is regenerated, and the `frontend` job fails until the types are. The committed contract carries a fixed `info.version`, so release-please never rewrites it; the live `/api/openapi.json` reports the release.
- `/api/meta` tells the client the version and whether this is the public demo (banner).
- Loading a demo goes through `DemoService`: demos in `app/demo/` with `assumptions` also get a first analysis, never with the LLM (RS-89). Reductions there are keyed by step name.

## Verify

```bash
uv run pytest tests/integration/api tests/unit/test_openapi_contract.py
```
