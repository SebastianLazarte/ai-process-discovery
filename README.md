# AI Process Discovery & Automation Planner

[![CI](https://github.com/SebastianLazarte/ai-process-discovery/actions/workflows/ci.yml/badge.svg)](https://github.com/SebastianLazarte/ai-process-discovery/actions/workflows/ci.yml)
[![CodeQL](https://github.com/SebastianLazarte/ai-process-discovery/actions/workflows/codeql.yml/badge.svg)](https://github.com/SebastianLazarte/ai-process-discovery/actions/workflows/codeql.yml)
[![Release](https://img.shields.io/github/v/release/SebastianLazarte/ai-process-discovery?include_prereleases)](https://github.com/SebastianLazarte/ai-process-discovery/releases)

Turns a business process described step by step into a quantified, explainable automation blueprint. Code computes every number. The LLM only interprets what is ambiguous, and it cannot remove a human control.

## Problem

Teams decide what to automate by intuition. Nobody measures how much time each step takes, which steps are technically suitable, which ones must keep a person in the loop, or whether the savings survive honest assumptions.

## What it does

```text
Describe the process
  → quantify the current state            (hours, cost)
  → deterministic automation assessment   (score, method, human control)
  → AI-assisted analysis                  (interpretation, risks, architecture)
  → human review                          (overrides with a reason)
  → automation blueprint                  (JSON and Markdown)
```

## Design principles

- **Deterministic first.** Hours, cost, scores, savings, payback and ROI come from Python with `Decimal` arithmetic.
- **Structured LLM output.** The model fills a Pydantic schema that has no field for any business number.
- **Human in the loop.** Rules decide the minimum human control. The AI may raise it, never lower it. People may override, with a reason that is stored next to the original.
- **Explainable scoring.** Every score keeps its factors, penalties, unknown inputs and policy version.
- **Provider abstraction.** Services depend on an `LLMProvider` protocol. A deterministic fake is the default.
- **API first.** The Streamlit UI is just another HTTP client.

## Architecture

```mermaid
flowchart TB
    UI[Streamlit UI] -->|REST JSON| API[FastAPI]
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

`app/domain/` imports no framework, ORM or SDK. A test fails if it does.

```mermaid
sequenceDiagram
    participant UI as Streamlit
    participant API as FastAPI
    participant A as AnalysisService
    participant D as Domain
    participant L as LLMProvider
    participant DB as Database
    UI->>API: POST /processes/{id}/analyses
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

If the provider times out, refuses or returns invalid output, the analysis is still stored with `llm_status=unavailable` and its deterministic part complete.

## Setup

Requires [uv](https://docs.astral.sh/uv/).

```bash
uv sync --all-extras
cp .env.example .env            # optional: LLM_PROVIDER=anthropic and a key

uv run uvicorn app.main:app --reload                 # API on :8000, docs at /docs
uv run streamlit run ui/streamlit_app.py             # UI on :8501
```

Or the whole stack with PostgreSQL:

```bash
docker compose up --build
```

Released images: `docker pull ghcr.io/sebastianlazarte/ai-process-discovery:latest`.

## Tests

```bash
uv run pytest                        # unit + integration, SQLite, fake LLM
DATABASE_URL=postgresql+psycopg://apd:apd@localhost:5432/apd uv run pytest tests/integration
uv run pytest -m llm -o addopts=""   # real Anthropic call, needs a key
uv run pre-commit run --all-files    # format, lint, types
```

## API

| Method | Path | Purpose |
|---|---|---|
| `POST` `GET` | `/processes` | Create, list |
| `GET` `PATCH` `DELETE` | `/processes/{id}` | Read, update, delete |
| `POST` | `/processes/{id}/steps` | Add a step (optionally at a position) |
| `PUT` | `/processes/{id}/steps/order` | Reorder steps |
| `PATCH` `DELETE` | `/steps/{id}` | Update, delete a step |
| `POST` `GET` | `/processes/{id}/analyses` | Run an analysis, history |
| `GET` | `/analyses/{id}` | Analysis with overrides applied |
| `POST` | `/analyses/{id}/overrides` | Human override with reason |
| `GET` | `/analyses/{id}/blueprint`, `/analyses/{id}/blueprint.md` | Blueprint as JSON or Markdown |
| `GET` `POST` | `/demo-processes`, `/demo-processes/{slug}` | Synthetic demo processes |
| `GET` | `/health` | Application and database state |

## Example

The `invoice-intake` demo: 400 invoices a month, 5 steps, 18.50 per hour.

| | Value |
|---|---|
| Current monthly hours | 95.33 |
| Current monthly cost | 1,763.67 |
| Process suitability | 65.9 / 100 |
| Hours freed at 60 % reduction | 57.20 |
| Net monthly savings (tooling 50) | 1,008.20 |
| Payback on 6,000 | 5.95 months |

The "Approve payment" step scores 60 and is `RULE_BASED`, and it still keeps `REQUIRED` human control because the step requires approval. The AI cannot change that.

## Trade-offs

- **SQLite locally, PostgreSQL in CI.** The demo runs with nothing but `uv`; the `test-postgres` job proves the PostgreSQL path on every pull request ([ADR 0002](docs/adr/0002-sqlite-locally-postgresql-in-ci.md)).
- **No migrations yet.** `create_all` until a schema is released.
- **Streamlit.** Enough UI to demonstrate the flow; replaceable because it only speaks HTTP ([ADR 0005](docs/adr/0005-streamlit-as-rest-client.md)).
- **One real LLM provider.** The interface is the deliverable; a second adapter is one module ([ADR 0004](docs/adr/0004-provider-agnostic-llm-anthropic-first.md)).
- **Synchronous LLM call.** Simple and adequate for one analysis at a time; a queue is the next step if analyses grow.

## CI/CD

GitHub Flow with a protected `main`. Every pull request runs formatting, lint, strict typing, tests on Python 3.12 and 3.13 with 85 % minimum coverage, the integration suite on PostgreSQL, a Docker build with a compose smoke test, CodeQL and dependency review. Pull request titles follow Conventional Commits. release-please turns merged changes into versioned releases and the image is published to GHCR with provenance and SBOM. Details in [ADR 0006](docs/adr/0006-github-flow-ci-and-releases.md) and [CONTRIBUTING](CONTRIBUTING.md).

## Roadmap

| Block | Content |
|---|---|
| B0 | Repository, CI/CD, planning |
| B1 | Domain and metrics |
| B2 | Deterministic scoring |
| B3 | Business case |
| B4 | Persistence and API |
| B5 | LLM layer |
| B6 | Reconciliation |
| B7 | Blueprint |
| B8 | Streamlit UI |
| B9 | Docs and 1.0 release |

Requirements and acceptance criteria: [docs/requirements.toml](docs/requirements.toml). Scope and non-goals: [PDR 001](docs/pdr/001-mvp-scope.md).

## License

MIT. All demo data is synthetic.
