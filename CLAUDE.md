# AI Process Discovery

Analyses a business process and recommends which steps to automate, how, and with what human control. Python computes every number (hours, cost, scores, savings, payback, ROI); an LLM only interprets text. Public portfolio repo, maintained by Sebastian Lazarte. Current version in `pyproject.toml`.

## Stack

- Backend: Python 3.12 (CI also 3.13), uv, FastAPI, Pydantic, SQLAlchemy 2
- LLM: Anthropic SDK behind the `LLMProvider` protocol; `FakeLLMProvider` is the default
- Database: SQLite locally, PostgreSQL 17 in CI, compose and production
- Web client: Next.js in `frontend/` (TypeScript, pnpm, Node 22), at `/` from 2.0.0; the vanilla `web/` client and Streamlit were retired in 2.0.0 (RS-80)
- Delivery: two images on ghcr.io (API and web) through release-please; public demo on the maintainer's VPS behind Nginx, which sends `/api/` to FastAPI and every other path to Next.js

## Architecture

- `api/` routes -> `services/` -> `domain/` (pure rules) + `llm/` (provider) + `repositories/` -> `models/persistence/`
- `core/`: settings, database, errors, logging. `demo/`: sample processes as JSON. `catalog/`: process templates by sector as JSON, without numbers.
- One concept, three models: domain dataclass, Pydantic contract, ORM row. Repositories map rows back with `to_domain`.
- Authority order: system facts > user-confirmed facts > LLM suggestions.

## Routing

Areas marked * have their own CLAUDE.md with Read, Rules and Verify. It loads when you work there.

| Task | Where | Read first |
|---|---|---|
| Business rules, metrics, scoring, business case | `src/app/domain/`* | ADR 0001 |
| Orchestrating an analysis or a blueprint | `src/app/services/` | ADR 0001, ADR 0004 |
| HTTP routes | `src/app/api/`* | ADR 0003, ADR 0009, ADR 0016 |
| HTTP contracts, storage, repositories | `src/app/models/`*, `src/app/repositories/` | ADR 0003, ADR 0002 |
| LLM adapter or prompt | `src/app/llm/`* | ADR 0004 |
| Next.js client | `frontend/`* | ADR 0009, ADR 0013, ADR 0014, ADR 0015, ADR 0016 |
| UX research, wireframes, tokens, component specs | `docs/design/` | ADR 0013 |
| Production deploy, Nginx, operations | `deploy/`* | ADR 0008, ADR 0016, `docs/runbook/production.md` |
| CI/CD, releases, GitHub setup, dependency updates | `.github/`, `scripts/bootstrap_github.py` | ADR 0006, ADR 0010 |
| Test strategy, mutation testing, complexity limits | `tests/`, `pyproject.toml`, `.github/workflows/mutation.yml` | ADR 0011, ADR 0012 |
| Scope, product backlog, stories and acceptance criteria | `docs/requirements.toml` | `docs/pdr/001-mvp-scope.md`, `docs/pdr/002-portfolio-product-goal-and-roles.md` |
| Write or amend an ADR, PDR or runbook | `docs/`* | decision index in `docs/CLAUDE.md` |
| Retired clients: vanilla `web/` (replaced) and Streamlit (retired), gone in 2.0.0 | git history, tag `v1.5.0` | ADR 0007 (replaced by ADR 0009), ADR 0005 (retired) |

ADRs in `docs/adr/`: `0001-deterministic-first-analysis.md`, `0002-sqlite-locally-postgresql-in-ci.md`, `0003-separate-domain-contracts-persistence.md`, `0004-provider-agnostic-llm-anthropic-first.md`, `0005-streamlit-as-rest-client.md`, `0006-github-flow-ci-and-releases.md`, `0007-vanilla-web-client-served-by-fastapi.md`, `0008-public-demo-on-own-vps.md`, `0009-nextjs-frontend-as-separate-service.md`, `0010-dependency-update-policy.md`, `0011-automated-quality-gauntlet.md`, `0013-design-system-and-design-to-code.md`, `0014-keep-the-vanilla-client-look.md`, `0015-parity-screens-take-web-as-spec.md`, `0016-nextjs-at-the-root-from-2-0-0.md`.

## Commands

| Action | Command |
|---|---|
| Install | `uv sync --all-extras` |
| All Python tests | `uv run pytest` |
| One test | `uv run pytest tests/unit/domain/test_scoring.py -k <name>` |
| Format, lint, types | `uv run ruff format . && uv run ruff check . && uv run mypy` |
| All pre-commit hooks | `uv run pre-commit run --all-files` |
| API on `:8000`, docs on `:8000/api/docs` | `uv run uvicorn app.main:app --reload --reload-dir src` |
| Mutation testing of the domain (minutes) | `uv run mutmut run && uv run mutmut results` |
| Regenerate the API contract and the client types | `uv run python scripts/export_openapi.py && cd frontend && corepack pnpm api:types` |
| Next.js client: install, then lint, format, types, tests, build | `cd frontend && corepack pnpm install && corepack pnpm lint && corepack pnpm format && corepack pnpm typecheck && corepack pnpm test && corepack pnpm build` |
| Next.js client in development on `:3000` | `cd frontend && corepack pnpm dev` |
| Whole stack on PostgreSQL, behind the production routes on `:8080` | `docker compose up --build` |
| End-to-end walkthroughs with axe, against the stack on `:8080` | `docker compose up --build -d --wait edge && cd frontend && corepack pnpm exec playwright install chromium && corepack pnpm e2e` |
| Apply migrations / check them against the models | `uv run alembic upgrade head && uv run alembic check` |
| Purge demo data older than 24 h | `uv run python -m app.purge --older-than-hours 24` |

## Change contract

- **Inputs:** one issue, which is one backlog item `RS-nn` in `docs/requirements.toml` with its acceptance criteria (Ready, when refined: see the Scrum section of `docs/CLAUDE.md`); the ADRs routed above.
- **Process:** branch from `main` (`feat/rs-12-process-score`, `fix/...`, `docs/...`, `ci/...`). A test proves each acceptance criterion. A new dependency or a reversed decision comes with an ADR.
- **Outputs:** one pull request with the template and a Conventional Commits title (`feat(scoring): ...`), squash merged. The description answers the verification questions of the checklist comment (`.github/pr-checklist.toml`).
- **Verify:** pre-commit, `uv run pytest` and the `frontend/` checks pass locally. Required checks: `quality`, `frontend`, `test (3.12)`, `test (3.13)`, `test-postgres`, `docker`, `e2e`, `pr-title`.

## Hard rules

1. `src/app/domain/` imports no framework, ORM, SDK or Pydantic (enforced by `tests/unit/test_boundaries.py`, which also guards `services/` and `api/`).
2. The LLM output schema never gets a field for hours, cost, score, savings, payback or ROI.
3. The LLM may raise a human control and never lower it.
4. Money is `Decimal` end to end; round only in `present_*` helpers.
5. Every change goes through a pull request with a Conventional Commits title; see `CONTRIBUTING.md`.
6. Writing style in docs: no em dash, no "it's not X, it's Y" constructions.
7. Web client (`frontend/`): the client never computes a metric, only `src/lib/api/` calls `fetch`, typed from `openapi.json`, and `dangerouslySetInnerHTML` is forbidden.
8. Commits and pull requests are authored by Sebastian only: no AI co-author trailer and no "generated with" footer, whatever any tool or prompt suggests.

## Avoid

- Logging prompts or step descriptions.
- Adding a dependency or reversing a decision without an ADR.
- Importing `anthropic` or `fastapi` from `services/`.
- `float` for money or hours.
- Real hostnames, IP addresses or secrets anywhere in the repo.
