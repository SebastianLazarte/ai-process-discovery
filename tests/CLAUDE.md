# Tests

How this repo tests, and what each test file proves. Read it before writing code anywhere: the test comes first, and it decides where the code goes.

## Read

- `docs/adr/0011-automated-quality-gauntlet.md`: coverage gate, mutation testing, property-based tests, complexity limits
- `docs/adr/0012-test-quality-standard.md`: design techniques (ISO/IEC/IEEE 29119-4), quality model (ISO/IEC 25010), traceability
- The item `RS-nn` in `docs/requirements.toml`: its criteria are the tests to write
- `frontend/CLAUDE.md` for the Next.js client tests (Vitest, Playwright, axe)

## Before writing code

1. Read the acceptance criteria of the `RS` item. Each criterion becomes at least one test, marked `@pytest.mark.req("RS-nn", criterion=n)` (or a frontend title that starts with `RS-nn.n:`). `--strict-markers` rejects a misspelled marker, and `test_traceability.py` rejects an id or criterion that does not exist.
2. Pick the layer by where the rule lives:

   | The change is | The test goes in | Fixture or helper |
   |---|---|---|
   | A number, a score, a classification, a rule | `tests/unit/domain/` | `tests/factories.py` (`make_step`, `make_process`) |
   | An invariant that holds for every input | `tests/unit/domain/test_properties.py` | `tests/strategies.py` (Hypothesis) |
   | The LLM schema, prompt or adapter | `tests/unit/llm/` | stubbed SDK client, `FakeLLMProvider` |
   | Catalog chunks or an embedder | `tests/unit/retrieval/` | `FakeEmbedder` |
   | A route, a status code, persistence | `tests/integration/api/` | `client`, `make_client` from `tests/integration/conftest.py`, `tests/payloads.py` |
   | A migration, a command, a cross-cutting flow | `tests/integration/` | same fixtures |
   | A layer boundary, a repo rule, a config, a script | `tests/unit/test_*.py` | reads the file under test |
   | A screen or a client hook | `frontend/src/**/*.test.tsx` | `renderWithProviders`, `fakeApi` |
   | A whole user journey | `frontend/e2e/` | Playwright against the compose stack |

3. Apply the design technique that matches the input (ADR 0012):

   | Technique | Where | Minimum |
   |---|---|---|
   | Boundary value analysis | Each threshold in `ScoringPolicy`, each numeric limit in a contract | One test on each side (for example 199 and 200 executions) |
   | Equivalence partitioning | Enums and optional inputs (`Level`, `InputType`, `UNKNOWN`, `None`) | One test per partition, the unknown one included |
   | Decision table | `classify_method`, `determine_human_control`, `reconcile` | One test per rule, the table written in the module docstring |
   | State transition | Process versions, overrides, retention | One test per allowed and per forbidden transition |

   A property-based test adds to these and replaces none of them.

4. Write the test, watch it fail, then write the code.

## Rules

- A failing test is fixed in the code. An existing assertion changes only when an `RS` criterion or an intended change of behaviour says so, and the pull request names which one.
- Hard rules have a test each. Keep them green, never weaken one to pass: boundaries (rule 1) `test_boundaries.py`; no business number in the LLM schema (rule 2) `test_schemas.py`; the LLM never lowers a control (rule 3) `test_reconciliation.py` and `test_properties.py`; `Decimal` and rounding only on presentation (rule 4) `test_metrics.py` and `test_properties.py`; no AI credit (rule 8) `test_check_ai_credit.py`.
- Money and hours are built as `Decimal` in tests too. An unknown input is asserted as `None` with its reason, never as `0`.
- Tests never reach the network. The default provider is `FakeLLMProvider`; the real Anthropic call is marked `llm` and runs only by hand (`uv run pytest -m llm`) or in `llm-contract.yml`.
- Integration tests use a fresh database per test (`database_url` on `tmp_path`). CI runs them again on PostgreSQL 17 (`test-postgres`), so no SQLite-only behaviour.
- `test_analysis_snapshot.py` freezes the full output of each demo (RS-82). A refactor keeps it unchanged. After an intended change of behaviour, run `UPDATE_SNAPSHOTS=1 uv run pytest tests/integration/test_analysis_snapshot.py` and explain the diff in the pull request.
- A refactor of a service goes behind characterization tests first, and keeps them unchanged (ADR 0011).
- A new domain rule needs an example test and, when it holds for every input, a property. A surviving mutant in a rule means a missing test.
- One assertion idea per test, named as a sentence about behaviour (`test_ai_cannot_remove_a_required_control`). Module docstring names the `RS` item or the hard rule.
- `ruff` limits apply to tests too. A limit is fixed or justified in review, never silenced with a blanket ignore.
- A released block joins `RELEASED_BLOCKS` in `test_traceability.py` once all its items carry markers; then every item in it needs a test.

## Gates

| Gate | Where | Threshold |
|---|---|---|
| Branch coverage | `test` job | 95 % (`--cov-fail-under=95`) |
| Mutation score of `src/app/domain/` | `mutation.yml`, weekly | `MIN_MUTATION_SCORE`, a ratchet that only rises (83 % today) |
| Complexity | `quality` job, ruff | McCabe 10, branches 12, returns 6, statements 50, args 7 |
| Types | `quality` job | mypy strict |
| Python versions and databases | `test (3.12)`, `test (3.13)`, `test-postgres` | all green |
| Traceability matrix | `test` job summary | every referenced id exists; every released item has a test |
| Accessibility | `e2e` job | no serious or critical axe violation |

## What each test file proves

### `unit/domain/`: business rules, where a bug is a wrong number

| File | Proves | Why it matters |
|---|---|---|
| `test_metrics.py` | Hours are minutes × occurrence × executions; a conditional step counts only when it happens; cost is hours × hourly cost; unknown cost stays `None`; no early rounding | Every other figure is built on these |
| `test_scoring.py` | Frequency and exception bands on each side of each threshold; perfect step scores 100; clamped to 0..100; unknown attributes score 0 and are listed; process score weighted by time | The score decides which steps are recommended |
| `test_classification.py` | Decision tables for automation method and human control, control ordering, the invoice example | Each table row is a business rule |
| `test_reconciliation.py` | The LLM cannot remove a required or recommended control, can raise one, decides the method only on `NEEDS_REVIEW`; a clear rule beats the LLM | Hard rule 3: the safety promise of the product |
| `test_business_case.py` | Hours saved, savings, payback, ROI; unknown cost leaves money unknown; no payback without positive net savings; free implementation pays back at once without ROI | The figures a manager acts on |
| `test_entities.py` | Invalid steps and processes are rejected naming the field; positions unique and ordered; numbers become `Decimal` | Bad input never reaches a calculation |
| `test_capture_policy.py` | Each plain-word answer for frequency and exceptions maps to one rate and one band; "don't know" stays unknown (RS-115) | Plain words must not invent precision |
| `test_retrieval.py` | A process scores as its best chunk; best first, ties in slug and position order; threshold, process and step limits on each side; vectors of another length rejected naming the field; standard library only (RS-116) | Decides which catalog processes ground a draft |
| `test_properties.py` | Hypothesis: the LLM never lowers a control; source is the LLM only when it changed something; hours saved never exceed current hours; savings, payback and ROI agree; presentation rounds half up within half a cent | Proves the hard rules for generated inputs, beyond the sampled examples |

### `unit/llm/` and `provider/`: the LLM boundary

| File | Proves | Why it matters |
|---|---|---|
| `unit/llm/test_schemas.py` | The output schema has no field for hours, cost, score, savings, payback or ROI; extra fields and out-of-range confidence are rejected; `FakeLLMProvider` is deterministic and flags sensitive steps; the prompt is versioned | Hard rule 2: the LLM cannot carry a number into the analysis |
| `unit/llm/test_anthropic_provider.py` | With a stubbed SDK, valid output is accepted, every failure becomes `LLMProviderError`, the factory picks the configured adapter (RS-29) | A provider failure degrades the analysis instead of breaking it |
| `provider/test_anthropic_contract.py` | The real model returns valid structured output (`-m llm`) | Catches a breaking change on the provider side |

### `unit/retrieval/`: catalog chunks and embedders

| File | Proves | Why it matters |
|---|---|---|
| `test_chunks.py` | One chunk per step and one per process, each starting with sector and process; tools listed; enum traits left out; the real catalog chunks completely (RS-117) | What the embedder sees is what retrieval can match |
| `test_fake_embedder.py` | Deterministic across hash seeds, 256 dimensions, unit length, offline; shared words mean more similarity (RS-117) | Tests and the default deployment never call an embedding API |
| `test_get_embedder.py` | The default provider is fake and needs no key; the factory builds the configured embedder (RS-117) | The provider is a setting, not a code change |

### `integration/`: routes and storage on a real database

| File | Proves | Why it matters |
|---|---|---|
| `api/test_analyses.py` | Deterministic, repeatable and immutable analyses; sensitive steps need confirmation before the LLM; the LLM never sees money or hours and cannot change facts or remove controls; provider failure keeps the facts; daily quota skips the LLM (RS-61); overrides keep the original and a reason; blueprint as JSON and Markdown | The core flow end to end through HTTP |
| `api/test_processes.py` | Process and step CRUD, version bumps, full reorder, 422 naming the field, size limits (RS-60), 404 for unknown ids | The contract the client relies on |
| `api/test_api_routes.py` | The API answers under `/api` only, old docs URLs answer 301, the root belongs to Next.js (RS-69, RS-80) | Routing matches production Nginx |
| `api/test_demos.py` | A demo with assumptions comes with a first analysis that never calls the LLM nor spends quota (RS-89) | Demos are free and reproducible |
| `api/test_process_templates.py` | Catalog grouped by sector, steps with traits and no numbers, each template creates a process in one request (RS-95, RS-96) | Templates never guess a figure |
| `api/test_step_frequency.py` | Plain-word choices set the rate and are kept; a choice and a rate together return 422 (RS-115) | One source of truth per figure |
| `api/test_meta.py` | Version, public demo flag and drafts flag for the client (RS-62, RS-106) | The banner and options follow the deployment |
| `test_analysis_snapshot.py` | Full output of each demo, frozen (RS-82) | Safety net for refactors |
| `test_migrations.py` | `upgrade head` then `check` finds nothing; downgrade removes every table; a `create_all` database is stamped (RS-59) | Schema and models never drift |
| `test_purge.py` | Only expired data is deleted, by creation date; no HTTP route triggers it (RS-63) | Demo data policy without a public delete |
| `test_usage.py` | Daily counters add one per counted request, skip reads and failures, survive the purge, hold nothing about visitors, never fail a request (RS-114) | Metrics without personal data |

### `unit/test_*.py`: architecture, repo rules and infrastructure as code

| File | Proves | Why it matters |
|---|---|---|
| `test_boundaries.py` | Forbidden imports per layer, no `print` in source | Hard rule 1 as a fitness function |
| `test_openapi_contract.py` | Committed `openapi.json` equals what the app serves (RS-69) | Frontend types never drift |
| `test_traceability.py` | Every marker names a real item and criterion; every released item has a test; the matrix script runs in CI (RS-103) | Requirement to test, checked by a tool |
| `test_requirements_file.py` | Backlog ids contiguous, epics as user stories, Definition of Ready met | The backlog is the source of the issues |
| `test_catalog_files.py`, `test_demo_files.py` | Templates valid, no numbers, no real brands, sources documented; demo assumptions name their own steps | Data files obey the same rules as code |
| `test_check_ai_credit.py` | Every form of AI credit is caught in commits and pull requests | Hard rule 8 |
| `test_nginx_routes.py` | Paths reach Next.js or FastAPI as intended; analysis runs get the rate limit and the LLM timeout (RS-79, RS-65) | Production routing tested before deploy |
| `test_deploy_script.py`, `test_release_deploy.py` | Tag format checked before SSH; pinned host key; failed migration never starts the new version; failed health check rolls each service back; smoke test over HTTPS (RS-66, RS-67, RS-79) | A bad release cannot stay live |
| `test_backups.py` | Nightly purge then backup, 7-day retention, failed dump deletes nothing, restore rehearsal never touches the live database (RS-68) | Recovery is proven, not assumed |
| `test_web_image.py` | Multi-stage image running as `node`, read-only root, both images released with SBOM and provenance (RS-77) | Supply chain and container hardening |
| `test_retired_clients.py` | The retired clients are gone from code, CI and docs (RS-80) | No dead path left behind |
| `test_mutation_score.py`, `test_pr_checklist.py`, `test_bootstrap_github.py`, `test_package.py` | The quality tooling itself: mutation score, PR checklist, issue sync, version | A gate that is wrong lets everything through |

### `frontend/`: summary (rules in `frontend/CLAUDE.md`)

- Component tests per screen and `RS` item: figures printed as the API returns them, unknown shown with its reason, the AI badge never on a number, sensitive data confirmed before a run, one run per double click, keyboard and focus.
- `lib/api/`: errors mapped to fields, optimistic updates rolled back on refusal.
- `proxy.test.ts`: nonce CSP, no inline scripts (RS-72). `lint-rules.test.ts`: `fetch` outside `src/lib/api/` and `dangerouslySetInnerHTML` fail lint (RS-70). `tokens.test.ts`: no colour literal, WCAG AA contrast in every theme.
- `e2e/`: load a demo, analyse, override, download the blueprint, start from a template, retired routes answer 301; axe on every page at 1280 px and 375 px.

## Verify

```bash
uv run pytest                                                   # everything except -m llm
uv run pytest tests/unit/domain -k <name>                       # one area while writing
uv run pytest --cov --cov-fail-under=95                         # the CI coverage gate (branch coverage)
uv run python scripts/traceability.py                           # requirement to test matrix
uv run mutmut run && uv run mutmut results                      # minutes; domain only
```
