# ADR 0012: Test quality standard

**Status:** accepted · 2026-10-17 · builds on ADR 0011; amends the Definition of Done (PDR 002)

## Context

ADR 0011 made the suite hard to fool: 95 % branch coverage as a gate, mutation testing of the domain with a rising minimum, property-based tests for the hard rules and complexity limits. Today 284 Python tests, 21 Node tests and the `frontend/` tests pass, with 98 % branch coverage (1,706 statements, 270 branches).

Those gates measure how strong the tests are. Three questions an outside reader asks still have no checkable answer:

- **Which standard are the tests designed against?** Test design follows good habits (boundary tests on the scoring bands, one test per reconciliation rule), but no document names the techniques a test must apply, so a reviewer cannot judge a new test against anything.
- **Which test proves which requirement?** The Definition of Done asks for one test per criterion, and the pull request checklist asks "Which test covers each acceptance criterion?". The answer stays in the pull request description. Only 24 of the 90 `RS` items are named in a test, and none of the 160 criteria (104 `acceptance` items, 56 Given/When/Then) can be traced to a test by a tool.
- **Is the LLM any good?** `tests/provider/` proves the real model returns a valid schema. No labelled dataset says what a correct recommendation is, so there is no task success rate, and cost per analysis has never been measured although the provider logs tokens.

The product goal (PDR 002) is a demo of software people can trust. Its quality claims need the same standard as its numbers: computed, reproducible and traceable.

## Decision

Three parts complete ADR 0011. Each ends in a test, a gate or a published report, so every claim about the suite comes from a command anyone can run.

### 1. Reference standards

- **ISO/IEC/IEEE 29119-4** names the test design techniques. Each applies where its input shape occurs:

  | Technique | Applies to | Minimum |
  |---|---|---|
  | Boundary value analysis | Every threshold in `ScoringPolicy` and every numeric limit in a contract | One test on each side of each boundary (for example 199 and 200 effective executions) |
  | Equivalence partitioning | Enums and optional inputs (`Level`, `InputType`, `UNKNOWN`, `None`) | One test per partition, including the unknown one |
  | Decision table testing | `classify_method`, `determine_human_control`, `reconcile` | One test per rule of the table, written down in the test module docstring |
  | State transition testing | Process versioning, overrides, retention | One test per allowed transition and one per forbidden one |

  Property-based tests (ADR 0011) complement these techniques and do not replace them: a generated case shows an invariant holds, a named boundary case shows the reader where the rule turns.

- **ISO/IEC 25010:2023** is the quality model. Each characteristic maps to the evidence that covers it, and the gaps are stated instead of hidden:

  | Characteristic | Evidence |
  |---|---|
  | Functional suitability | Unit and integration tests, traceability (part 2), task success rate (part 3) |
  | Reliability | Tests for every `LLMProviderError` path: the analysis degrades and every figure still comes out |
  | Safety | Hard rules 2 and 3 as example and property tests; zero lowered controls in the eval (part 3) |
  | Security | Sensitive data confirmation tests, CodeQL, dependency review, output escaping tests |
  | Compatibility | Python 3.12 and 3.13 matrix, `test-postgres` |
  | Maintainability | `test_boundaries.py`, ruff complexity limits, mypy, coverage and mutation score (ADR 0011) |
  | Interaction capability | WCAG 2.2 AA under ADR 0013, tested in `frontend/` |
  | Performance efficiency | Not gated yet; the eval report records latency per analysis |
  | Flexibility | `LLMProvider` protocol with two implementations under the same tests |

### 2. Requirement traceability

- A test that proves a criterion carries a marker: `@pytest.mark.req("RS-12")`, or `@pytest.mark.req("RS-70", criterion=2)` for a refined item with Given/When/Then criteria. Node and `frontend/` tests put the id at the start of the test name (`"RS-58: ..."`).
- `tests/unit/test_traceability.py` checks that every referenced id and criterion number exists in `docs/requirements.toml`, and that every item in a released block has at least one test. The list of released blocks lives in that test and widens with each release, like the block list in `test_requirements_file.py`.
- `scripts/traceability.py` prints the matrix (item, criterion, tests) as Markdown. CI adds it to the job summary.
- When the marker and the traceability test land, the Definition of Done in `docs/CLAUDE.md` changes from "one test per criterion" to "one marked test per criterion". The checklist question about criteria stays, and the reviewer can now check the answer against the matrix.

### 3. LLM evaluation

- `tests/evals/dataset/` holds processes as JSON with a label per step: expected method and expected human control. The Product Owner writes and approves the labels, because a correct recommendation is a product decision. The demo processes are the first cases; the dataset grows to at least 30 labelled steps before any metric is published.
- Metrics, all computed in Python:
  - **Task success rate**: share of labelled steps where the final method and the final human control both match the label. It is reported twice, rules only and rules with the LLM, so the model's contribution is visible.
  - **Lowered controls**: steps where the final control is weaker than the label. The gate is zero.
  - **Schema validity rate**: share of real calls that return valid output.
  - **Latency and cost per analysis**: from the logged `input_tokens` and `output_tokens`, priced with the provider's published rates on the day of the run, written in the report with that date. Money stays `Decimal`.
- The rules-only run uses `FakeLLMProvider` and runs in every CI build. Its task success rate is a regression gate: it may not drop below the last accepted value unless the same pull request updates that value and says why.
- The real-model run is a manual workflow next to `llm-contract.yml`, with a run cap so it stays inside the daily budget. Each run writes `docs/quality/eval-YYYY-MM-DD.md` with the model, prompt version, rules version, dataset version and every metric.

## Consequences

- Each figure in the README or a portfolio becomes a link to a command or a report: coverage and mutation score (ADR 0011), traceability, task success rate, cost.
- The released items not yet referenced by any test need markers before the released-block check can pass. That backfill is planned work, one backlog item per block or per area.
- The dataset labels are the Product Owner's work. Until 30 steps are labelled, the eval reports only the rules-only run and no success rate is published.
- `pyproject.toml` gains a `req` marker. `--strict-markers` already rejects a misspelled one.
- No new dependency: the traceability check and the eval metrics are plain Python over the existing contracts.

## Alternatives rejected

| Option | Why not |
|---|---|
| Requirement ids in test names only | Readable, but a typo goes unnoticed; a marker is checked by `--strict-markers` and by the traceability test |
| Traceability per item only, without criterion numbers | Simpler, but an item with five criteria and one test would pass |
| A third-party eval framework | Adds a dependency and its own metric definitions; the metrics needed here are a few lines of Python |
| LLM-as-judge for the eval | The labels are discrete (method, control), so exact matching is enough and adds no second model to trust |
| Labels written by an agent | A label states what the right recommendation is, which is a product decision (PDR 002) |
