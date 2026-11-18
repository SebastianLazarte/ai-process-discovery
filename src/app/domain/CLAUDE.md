# Domain

Business behaviour as plain Python: metrics, scoring, method classification, human control, business case and reconciliation of rules with the LLM. Frozen dataclasses and `Decimal`, nothing else, apart from the similarity of `retrieval.py`.

## Read

- `docs/adr/0001-deterministic-first-analysis.md`
- `policies.py`: `ScoringPolicy` and its `version`, which every analysis records as `policy_version`

## Rules

- Hard rule 1: no framework, ORM, SDK, Pydantic or other `app` layer (`llm`, `models`, `repositories`, `services`, `api`).
- Hard rule 4: arithmetic stays exact; rounding happens only in the `present_*` functions of `decimals.py`.
- Hard rule 3: `reconciliation.py` lets the LLM raise a human control, never lower it, and decide a method only where the rules return `NEEDS_REVIEW`.
- `retrieval.py` ranks catalog processes by cosine similarity, a `float` that never touches money or hours (ADR 0021); it imports only the stdlib and `app.domain`.
- Every figure must still come out with the LLM off or failing (`llm_status=unavailable`).
- Unknown inputs stay unknown and are reported; they are never guessed.
- A new rule gets an example test and, when it holds for every input, a property in `tests/unit/domain/test_properties.py` (ADR 0011).

## Verify

```bash
uv run pytest tests/unit/domain tests/unit/test_boundaries.py
uv run mutmut run && uv run mutmut results   # minutes; a surviving mutant in a rule means a missing test
```
