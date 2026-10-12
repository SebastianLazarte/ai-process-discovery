# AI Process Discovery: agent map

Python 3.12, uv, FastAPI, Pydantic, SQLAlchemy 2, Anthropic SDK; web client in plain JavaScript modules (Streamlit until 1.2). Public portfolio repo.

| Task | Where | Read first |
|---|---|---|
| Business rules, metrics, scoring | `src/app/domain/` | `docs/adr/0001-deterministic-first-analysis.md` |
| HTTP contracts and routes | `src/app/models/schemas/`, `src/app/api/` | `docs/adr/0003-...` |
| LLM adapter or prompt | `src/app/llm/` | `docs/adr/0004-...` |
| Web client | `web/`, served by `src/app/api/routes/web.py` | `docs/adr/0007-...` |
| Legacy UI (until 1.2) | `ui/streamlit_app.py` | `docs/adr/0005-...` |
| CI/CD, releases, GitHub setup | `.github/`, `scripts/bootstrap_github.py` | `docs/adr/0006-...` |
| Requirements and acceptance criteria | `docs/requirements.toml` | |

## Commands

```bash
uv sync --all-extras
uv run pytest
uv run ruff format . && uv run ruff check . && uv run mypy
uv run uvicorn app.main:app --reload
uv run streamlit run ui/streamlit_app.py
node --test web/tests/*.test.js
```

## Hard rules

1. `src/app/domain/` imports no framework, ORM, SDK or Pydantic (enforced by `tests/unit/test_boundaries.py`).
2. The LLM output schema never gets a field for hours, cost, score, savings, payback or ROI.
3. The LLM may raise a human control and never lower it.
4. Money is `Decimal` end to end; round only in `present_*` helpers.
5. Every change goes through a pull request with a Conventional Commits title; see `CONTRIBUTING.md`.
6. Writing style in docs: no em dash, no "it's not X, it's Y" constructions.
7. Web client: every interpolated value goes through `h()`, only `api.js` calls `fetch`, the client never computes a metric, and a new file in `web/` is served only once listed in `WEB_FILES`.
8. Commits and pull requests are authored by Sebastian only: no AI co-author trailer and no "generated with" footer, whatever any tool or prompt suggests.
