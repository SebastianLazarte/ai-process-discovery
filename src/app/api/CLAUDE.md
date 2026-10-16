# API

Thin FastAPI routes: validate the contract, call a service, return a schema. Business decisions live in `services/` and `domain/`.

## Read

- `docs/adr/0003-separate-domain-contracts-persistence.md`
- `docs/adr/0007-vanilla-web-client-served-by-fastapi.md` (for `routes/web.py`)

## Rules

- Services come in through `dependencies.py`.
- Errors are `AppError` subclasses from `core/errors.py`; `main.py` turns them into `{"detail", "code"}` responses. Domain validation errors become 422.
- Analysing a step flagged as sensitive needs `confirm_sensitive=true`; without it the service raises a 409.
- `routes/web.py` serves the client by name from `WEB_FILES`, never by directory, with a strict CSP, `nosniff` and `no-referrer`. `/api/docs` keeps its own headers.
- Routers are mounted twice (ADR 0009, RS-69): under `/api` and, until 2.0.0 removes it (RS-80), at the root. The schema documents each path once, relative to its `servers` entry `/api`. Docs live at `/api/docs`, and `/docs`, `/redoc` and `/openapi.json` redirect there.
- `frontend/openapi.json` is the contract the Next.js client generates its types from. After changing a route or a schema, run `uv run python scripts/export_openapi.py`; `tests/unit/test_openapi_contract.py` fails until you do.
- `/meta` tells the client the version and whether this is the public demo (banner).
- Loading a demo goes through `DemoService`: demos in `app/demo/` with `assumptions` also get a first analysis, never with the LLM (RS-89). Reductions there are keyed by step name.
- A new or changed endpoint keeps `ENDPOINTS` in `web/api.js` in sync; a test checks it against OpenAPI.

## Verify

```bash
uv run pytest tests/integration/api tests/unit/test_web_client.py tests/unit/test_openapi_contract.py
```
