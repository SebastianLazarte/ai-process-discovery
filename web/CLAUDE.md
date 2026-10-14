# Web client

ES modules served by FastAPI at `/ui/`. No framework, no bundler, no `package.json`, no dependencies.

Legacy: ADR 0009 replaces this client with `frontend/` and removes it in 2.0.0. Fixes only, no new features.

## Read

- `docs/adr/0007-vanilla-web-client-served-by-fastapi.md`
- `docs/adr/0009-nextjs-frontend-as-separate-service.md` (what replaces it)

## Rules

- Hard rule 7, in detail:
  - Views are pure functions that return HTML strings, and every interpolated value goes through `h()`.
  - `api.js` is the only module that calls `fetch`, and it names every endpoint in `ENDPOINTS`.
  - The client never computes a metric. `format.js` prints the figures the API returns and is the only module that turns strings into numbers. Form inputs travel to the API as strings.
  - A new file here is served only once listed in `WEB_FILES` in `src/app/api/routes/web.py`.
- No inline script, inline style or `style` attribute: the CSP is `script-src 'self'; style-src 'self'`.
- Option lists match the domain enums.
- Browser walkthroughs are recorded in the pull request.

## Verify

```bash
node --test web/tests/*.test.js
uv run pytest tests/unit/test_web_client.py tests/integration/api/test_web.py
```
