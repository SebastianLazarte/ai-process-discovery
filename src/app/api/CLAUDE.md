# API

Thin FastAPI routes: validate the contract, call a service, return a schema. Business decisions live in `services/` and `domain/`.

## Read

- `docs/adr/0003-separate-domain-contracts-persistence.md`
- `docs/adr/0007-vanilla-web-client-served-by-fastapi.md` (for `routes/web.py`)

## Rules

- Services come in through `dependencies.py`.
- Errors are `AppError` subclasses from `core/errors.py`; `main.py` turns them into `{"detail", "code"}` responses. Domain validation errors become 422.
- Analysing a step flagged as sensitive needs `confirm_sensitive=true`; without it the service raises a 409.
- `routes/web.py` serves the client by name from `WEB_FILES`, never by directory, with a strict CSP, `nosniff` and `no-referrer`. `/docs` keeps its own headers.
- `/meta` tells the client the version and whether this is the public demo (banner).
- A new or changed endpoint keeps `ENDPOINTS` in `web/api.js` in sync; a test checks it against OpenAPI.

## Verify

```bash
uv run pytest tests/integration/api tests/unit/test_web_client.py
```
