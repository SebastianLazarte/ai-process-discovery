# AI Process Discovery & Automation Planner

[![CI](https://github.com/SebastianLazarte/ai-process-discovery/actions/workflows/ci.yml/badge.svg)](https://github.com/SebastianLazarte/ai-process-discovery/actions/workflows/ci.yml)
[![CodeQL](https://github.com/SebastianLazarte/ai-process-discovery/actions/workflows/codeql.yml/badge.svg)](https://github.com/SebastianLazarte/ai-process-discovery/actions/workflows/codeql.yml)
[![Release](https://img.shields.io/github/v/release/SebastianLazarte/ai-process-discovery?include_prereleases)](https://github.com/SebastianLazarte/ai-process-discovery/releases)

Describe a business process step by step and get a quantified, explainable automation plan: which steps to automate, how, what it saves, and where a person must stay in control.

**Code computes every number. The AI only interprets, and it can never remove a human control.**

## Try it

**Live demo:** the Website link at the top of this repository's page, once the public demo is online. No sign-up, synthetic data, deleted every night ([data policy](SECURITY.md#public-demo-data)).

**On your machine** (Docker, no API key needed), from a clone of this repository:

```bash
docker compose up --build
```

Then open <http://localhost:8080/>. The API docs are at <http://localhost:8080/api/docs>.

## A two-minute tour

The demos follow a fictitious manufacturer of zoned HVAC controls that sells through distributors and installers. The processes, volumes and costs are synthetic but modelled on how such a company works. Each demo loads with its assumptions already set and a first analysis already run.

| Demo | Per month | Today | Net savings | Payback |
|---|---|---|---|---|
| Order intake from distributors | 1,100 orders | 278.30 h, 5,844.30 | 3,888.85 | 7.20 months |
| Zoning design and quote for installers | 240 quotes | 308.00 h, 9,856.00 | 3,641.20 | 9.61 months |
| Warranty claims from installers | 320 claims | 180.00 h, 4,320.00 | 1,384.80 | 15.89 months |

1. **Load "Warranty claims from installers".** The results open straight away, in four separate answers: current cost, suitability (42.1 / 100), business impact and human controls.
2. **Read the human controls.** "Approve the credit note or free replacement" is `RULE_BASED` and still keeps `REQUIRED` human control, because the step needs an approval. The lab inspection stays `MANUAL`: the input is a physical unit. The AI cannot change either.
3. **Notice the payback.** Automation suits this process less than order intake, and the 12-month ROI is negative. Suitability and savings are reported apart on purpose.
4. **Run it again with your own assumptions and the LLM.** On Analyse, enter costs and reductions, tick "Enrich with the LLM" and confirm the notice about steps with sensitive data. Without a key, a deterministic fake provider plays the LLM.
5. **Override a recommendation** on any step. The reason is mandatory and is stored next to the original.
6. **Open Blueprint** and download it as Markdown: eight sections, ready to hand to a team.

## Why it is built this way

Teams decide what to automate by intuition, and LLMs make it tempting to let a model produce the numbers. This project takes the opposite position:

- **Deterministic first.** Hours, cost, scores, savings, payback and ROI come from Python with `Decimal` arithmetic ([ADR 0001](docs/adr/0001-deterministic-first-analysis.md)).
- **The LLM cannot produce a business number.** Its output is a Pydantic schema with no field for hours, cost, score, savings, payback or ROI, and it never sees monetary inputs.
- **Human in the loop.** Rules set the minimum human control. The AI may raise it, never lower it. People may override with a reason.
- **Explainable scoring.** Every score keeps its factors, penalties, unknown inputs and policy version. Unknown values are reported, never invented.
- **Degrades gracefully.** If the provider times out, refuses or returns invalid output, the analysis is still stored with its deterministic part complete.

## For engineers: where to look

| To see | Open |
|---|---|
| The scoring rules, as pure functions | [`src/app/domain/scoring.py`](src/app/domain/scoring.py), [`policies.py`](src/app/domain/policies.py) |
| How rules and AI are reconciled (raise, never lower) | [`src/app/domain/reconciliation.py`](src/app/domain/reconciliation.py) |
| The LLM output schema with no room for numbers | [`src/app/llm/schemas.py`](src/app/llm/schemas.py) and its test [`test_schemas.py`](tests/unit/llm/test_schemas.py) |
| A test that fails if the domain imports a framework | [`tests/unit/test_boundaries.py`](tests/unit/test_boundaries.py) |
| Property-based tests of the domain | [`tests/unit/domain/test_properties.py`](tests/unit/domain/test_properties.py) |
| Every decision and its trade-offs | [`docs/adr/`](docs/adr/) |
| The product backlog with Given/When/Then criteria | [`docs/requirements.toml`](docs/requirements.toml) |

Quality bar on every pull request: formatting, lint, strict typing, tests on Python 3.12 and 3.13 with 95 % minimum coverage and complexity limits, the integration suite on PostgreSQL, the Next.js client's lint, types, tests and build on Node 22, Docker builds with a smoke test, end-to-end walkthroughs with axe through the production routes, CodeQL and dependency review. A weekly job runs mutation testing on the domain ([ADR 0011](docs/adr/0011-automated-quality-gauntlet.md)). Releases are versioned by release-please and the API and Next.js images ship to GHCR with the same tag, provenance and SBOM ([ADR 0006](docs/adr/0006-github-flow-ci-and-releases.md)).

## Architecture

```mermaid
flowchart TB
    NGINX[Nginx] -->|/| WEB[Next.js client]
    NGINX -->|/api/| API[FastAPI]
    WEB -->|REST JSON /api/| API
    API --> PS[ProcessService]
    API --> AS[AnalysisService]
    API --> BS[Blueprint]
    AS --> DOM[Domain: metrics, scoring, classification, business case, reconciliation]
    AS --> LLM[LLMProvider]
    LLM --> FAKE[FakeLLMProvider]
    LLM --> ANT[AnthropicProvider]
    PS --> REPO[Repositories]
    AS --> REPO
    REPO --> DB[(SQLite / PostgreSQL)]
```

Nginx sends `/api/` to FastAPI and every other path to the Next.js client, and an old `/ui/` link answers 301 to `/` ([ADR 0016](docs/adr/0016-nextjs-at-the-root-from-2-0-0.md)). `app/domain/` imports no framework, ORM or SDK. A test fails if it does.

```mermaid
sequenceDiagram
    participant UI as Web client
    participant API as FastAPI
    participant A as AnalysisService
    participant D as Domain
    participant L as LLMProvider
    participant DB as Database
    UI->>API: POST /api/processes/{id}/analyses
    API->>A: run(process_id, assumptions)
    A->>DB: load process snapshot
    A->>D: metrics, scores, method, human control, business case
    A->>L: interpret steps (no money, no hours)
    L-->>A: validated structured output
    A->>D: reconcile(rules, AI)
    A->>DB: store immutable analysis
    API-->>UI: suitability, impact, risk, human controls
```

## Domain model

| Concept | Domain | API contract | Storage |
|---|---|---|---|
| Process | `Process` | `ProcessCreate` / `ProcessRead` / `ProcessUpdate` | `ProcessORM` |
| Step | `ProcessStep` | `StepCreate` / `StepRead` / `StepUpdate` | `ProcessStepORM` |
| Analysis | `DeterministicAssessment` + reconciliation | `AnalysisRead` | `AnalysisORM` (immutable, JSON result) |
| Human review | `RecommendationSource.HUMAN` | `OverrideCreate` / `OverrideOut` | `OverrideORM` |
| Business case | `BusinessCaseAssumptions` / `BusinessCase` | `BusinessCaseInput` / `BusinessImpactOut` | part of the analysis |

Each step carries the facts the rules need: duration, occurrence rate, repetitiveness, rule clarity, input type, exception rate, integration readiness, human judgement, human approval, sensitive data and criticality. Unknown values are allowed and reported, never invented.

## Scoring (`scoring-v1`)

| Factor | Max |
|---|---:|
| Frequency (effective executions per month) | 20 |
| Repetitiveness | 20 |
| Rule clarity | 20 |
| Digital input | 15 |
| Low exception rate | 15 |
| Integration readiness | 10 |

Penalties: human judgement −25, sensitive data −10, high criticality −15. The result is clamped to 0..100. The process score is the time-weighted mean of step scores, so a step that takes 70 % of the time weighs 70 %.

The weights are a product policy (`app/domain/policies.py`), versioned and replaceable without touching the algorithm. Suitability is never presented as savings: a step can score 95 and save three minutes a month.

Method classification, first match wins:

| Condition | Method |
|---|---|
| High rule clarity, structured digital input, known exception rate ≤ 10 % | `RULE_BASED` |
| Good integration available | `API_INTEGRATION` |
| Unstructured digital input, no human judgement | `AI_CANDIDATE` |
| Physical input, no integration | `MANUAL` |
| Anything else | `NEEDS_REVIEW` (the AI may decide here) |

## AI boundary

| The LLM does | The LLM does not |
|---|---|
| Interpret each step | Compute hours, cost, savings, payback or ROI |
| Suggest a method where rules say `NEEDS_REVIEW` | Override a clear rule |
| List dependencies, risks and uncertainties | Lower a human control |
| Suggest architecture components | See hourly cost or any monetary input |

## Run from source

Requires [uv](https://docs.astral.sh/uv/).

```bash
uv sync --all-extras
cp .env.example .env            # optional: LLM_PROVIDER=anthropic and a key
uv run uvicorn app.main:app --reload --reload-dir src
```

The API docs are on <http://localhost:8000/api/docs>. The default `FakeLLMProvider` is deterministic and needs no key.

The Next.js client, in a second terminal (Node 22, pnpm through corepack), on <http://localhost:3000/>. In development it sends `/api/` to the API on `:8000`:

```bash
cd frontend
corepack pnpm install
corepack pnpm dev
```

The whole stack with PostgreSQL, behind the production routes on <http://localhost:8080/>:

```bash
docker compose up --build
```

## Tests

```bash
uv run pytest                        # unit + integration, SQLite, fake LLM
DATABASE_URL=postgresql+psycopg://apd:apd@localhost:5432/apd uv run pytest tests/integration
uv run pytest -m llm -o addopts=""   # real Anthropic call, needs a key
uv run pre-commit run --all-files    # format, lint, types
cd frontend && corepack pnpm lint && corepack pnpm typecheck && corepack pnpm test   # Next.js client, Node 22
```

The end-to-end walkthroughs run with Playwright and axe against the whole stack: `docker compose up --build -d --wait edge`, then `corepack pnpm exec playwright install chromium && corepack pnpm e2e` in `frontend/`.

## API

Every path lives under `/api`. The old root paths of 1.x are gone in 2.0.0; `/docs`, `/redoc` and `/openapi.json` answer 301 to their `/api` counterparts.

| Method | Path | Purpose |
|---|---|---|
| `POST` `GET` | `/api/processes` | Create, list |
| `GET` `PATCH` `DELETE` | `/api/processes/{id}` | Read, update, delete |
| `POST` | `/api/processes/{id}/steps` | Add a step (optionally at a position) |
| `PUT` | `/api/processes/{id}/steps/order` | Reorder steps |
| `PATCH` `DELETE` | `/api/steps/{id}` | Update, delete a step |
| `POST` `GET` | `/api/processes/{id}/analyses` | Run an analysis, history |
| `GET` | `/api/analyses/{id}` | Analysis with overrides applied |
| `POST` | `/api/analyses/{id}/overrides` | Human override with reason |
| `GET` | `/api/analyses/{id}/blueprint`, `/api/analyses/{id}/blueprint.md` | Blueprint as JSON or Markdown |
| `GET` `POST` | `/api/demo-processes`, `/api/demo-processes/{slug}` | Synthetic demo processes |
| `GET` | `/api/meta` | Version and whether this is the public demo |
| `GET` | `/api/health` | Application and database state |

## Trade-offs

- **SQLite locally, PostgreSQL in CI.** The demo runs with nothing but `uv`; the `test-postgres` job proves the PostgreSQL path on every pull request ([ADR 0002](docs/adr/0002-sqlite-locally-postgresql-in-ci.md)).
- **Migrations in production, `create_all` locally.** Alembic owns the production schema and runs from the release image before a new version starts (RS-59); local runs and tests still create tables on startup, and a test fails if the models and the migrations disagree.
- **Next.js client as its own service.** The client prints the API's numbers and never computes one; its types are generated from the committed OpenAPI contract, and every page carries a strict CSP with a nonce ([ADR 0009](docs/adr/0009-nextjs-frontend-as-separate-service.md)). It replaced, in 2.0.0, a framework-free client that FastAPI served at `/ui/` ([ADR 0007](docs/adr/0007-vanilla-web-client-served-by-fastapi.md)), with the same look ([ADR 0014](docs/adr/0014-keep-the-vanilla-client-look.md)) and the same screens ([ADR 0015](docs/adr/0015-parity-screens-take-web-as-spec.md)). The Streamlit UI left at the same time.
- **One real LLM provider.** The interface is the deliverable; a second adapter is one module ([ADR 0004](docs/adr/0004-provider-agnostic-llm-anthropic-first.md)).
- **Synchronous LLM call.** Simple and adequate for one analysis at a time; a queue is the next step if analyses grow.

## Roadmap

| Block | Content | Status |
|---|---|---|
| B0 to B9 | Domain, scoring, business case, API, LLM layer, reconciliation, blueprint, 1.0 release | Done |
| B10 | Web client | Done (1.1) |
| B11 | Public demo: limits, LLM quota, demo banner, purge, production compose and Nginx | Done (1.2, 1.3) |
| B11 | Public demo: demos with preset assumptions (RS-89), Alembic migrations (RS-59), deploy script with rollback (RS-66), deploy from the release workflow with an HTTPS smoke test (RS-67) | Done |
| B11 | Public demo: nightly backups and purge on timers, restore rehearsal script, data policy (RS-68) | Done; first rehearsal recorded on 2026-10-21 |
| B12 | Next.js client at `/` and API under `/api`; vanilla and Streamlit clients retired | Done (2.0) |
| B13 | Quality gauntlet and refactors | In progress |

Requirements and acceptance criteria: [docs/requirements.toml](docs/requirements.toml). Scope and non-goals: [PDR 001](docs/pdr/001-mvp-scope.md). Product Goal and roles: [PDR 002](docs/pdr/002-portfolio-product-goal-and-roles.md). Contributing: [CONTRIBUTING](CONTRIBUTING.md).

## License

MIT. All demo data is synthetic.
