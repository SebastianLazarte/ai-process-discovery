# AI Process Discovery

Analyses a business process and recommends which steps to automate, how, and with what human control. Python computes every number (hours, cost, scores, savings, payback, ROI); an LLM only interprets text. Public portfolio repo, maintained by Sebastian Lazarte. Current version in `pyproject.toml`.

## Stack

- Backend: Python 3.12 (CI also 3.13), uv, FastAPI, Pydantic, SQLAlchemy 2
- LLM: Anthropic SDK behind the `LLMProvider` protocol; `FakeLLMProvider` is the default
- Database: SQLite locally, PostgreSQL 17 in CI, compose and production
- Web client: ES modules in `web/`, no framework, no build step, tests on Node 22
- Delivery: image on ghcr.io through release-please; public demo on the maintainer's VPS behind Nginx

## Architecture

- `api/` routes -> `services/` -> `domain/` (pure rules) + `llm/` (provider) + `repositories/` -> `models/persistence/`
- `core/`: settings, database, errors, logging. `demo/`: sample processes as JSON.
- One concept, three models: domain dataclass, Pydantic contract, ORM row. Repositories map rows back with `to_domain`.
- Authority order: system facts > user-confirmed facts > LLM suggestions.

## Routing

Areas marked * have their own CLAUDE.md with Read, Rules and Verify. It loads when you work there.

| Task | Where | Read first |
|---|---|---|
| Business rules, metrics, scoring, business case | `src/app/domain/`* | ADR 0001 |
| Orchestrating an analysis or a blueprint | `src/app/services/` | ADR 0001, ADR 0004 |
| HTTP routes, serving the client | `src/app/api/`* | ADR 0003, ADR 0007 |
| HTTP contracts, storage, repositories | `src/app/models/`*, `src/app/repositories/` | ADR 0003, ADR 0002 |
| LLM adapter or prompt | `src/app/llm/`* | ADR 0004 |
| Web client | `web/`* | ADR 0007 |
| Production deploy, Nginx, operations | `deploy/`* | ADR 0008, `docs/runbook/production.md` |
| CI/CD, releases, GitHub setup | `.github/`, `scripts/bootstrap_github.py` | ADR 0006 |
| Scope, requirements, acceptance criteria | `docs/requirements.toml` | `docs/pdr/001-mvp-scope.md` |
| Write or amend an ADR, PDR or runbook | `docs/`* | decision index in `docs/CLAUDE.md` |
| Streamlit UI: legacy, pending removal, no new features | `ui/streamlit_app.py` | ADR 0005 |

ADRs in `docs/adr/`: `0001-deterministic-first-analysis.md`, `0002-sqlite-locally-postgresql-in-ci.md`, `0003-separate-domain-contracts-persistence.md`, `0004-provider-agnostic-llm-anthropic-first.md`, `0005-streamlit-as-rest-client.md`, `0006-github-flow-ci-and-releases.md`, `0007-vanilla-web-client-served-by-fastapi.md`, `0008-public-demo-on-own-vps.md`.

## Commands

| Action | Command |
|---|---|
| Install | `uv sync --all-extras` |
| All Python tests | `uv run pytest` |
| One test | `uv run pytest tests/unit/domain/test_scoring.py -k <name>` |
| Format, lint, types | `uv run ruff format . && uv run ruff check . && uv run mypy` |
| All pre-commit hooks | `uv run pre-commit run --all-files` |
| API and web client on `:8000/ui/` | `uv run uvicorn app.main:app --reload` |
| Web client tests | `node --test web/tests/*.test.js` |
| Whole stack on PostgreSQL | `docker compose up --build` |
| Legacy Streamlit on `:8501` | `uv run streamlit run ui/streamlit_app.py` |

## Change contract

- **Inputs:** one issue, which is one requirement `RS-nn` in `docs/requirements.toml` with its acceptance criteria; the ADRs routed above.
- **Process:** branch from `main` (`feat/rs-12-process-score`, `fix/...`, `docs/...`, `ci/...`). A test proves each acceptance criterion. A new dependency or a reversed decision comes with an ADR.
- **Outputs:** one pull request with the template and a Conventional Commits title (`feat(scoring): ...`), squash merged. The description answers the verification questions of the checklist comment (`.github/pr-checklist.toml`).
- **Verify:** pre-commit, `uv run pytest` and the Node tests pass locally. Required checks: `quality`, `web`, `test (3.12)`, `test (3.13)`, `test-postgres`, `docker`, `pr-title`.

## Hard rules

1. `src/app/domain/` imports no framework, ORM, SDK or Pydantic (enforced by `tests/unit/test_boundaries.py`, which also guards `services/` and `ui/`).
2. The LLM output schema never gets a field for hours, cost, score, savings, payback or ROI.
3. The LLM may raise a human control and never lower it.
4. Money is `Decimal` end to end; round only in `present_*` helpers.
5. Every change goes through a pull request with a Conventional Commits title; see `CONTRIBUTING.md`.
6. Writing style in docs: no em dash, no "it's not X, it's Y" constructions.
7. Web client: every interpolated value goes through `h()`, only `api.js` calls `fetch`, the client never computes a metric, and a new file in `web/` is served only once listed in `WEB_FILES`.
8. Commits and pull requests are authored by Sebastian only: no AI co-author trailer and no "generated with" footer, whatever any tool or prompt suggests.

## Avoid

- Logging prompts or step descriptions.
- Adding a dependency or reversing a decision without an ADR.
- Importing `app` from `ui/`, or `anthropic` or `fastapi` from `services/`.
- `float` for money or hours.
- Real hostnames, IP addresses or secrets anywhere in the repo.
- New features in `ui/`.
