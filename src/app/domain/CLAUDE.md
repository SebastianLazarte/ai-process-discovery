# Domain

Business behaviour as plain Python: metrics, scoring, method classification, human control, business case and reconciliation of rules with the LLM. Frozen dataclasses and `Decimal`, nothing else.

## Read

- `docs/adr/0001-deterministic-first-analysis.md`
- `policies.py`: `ScoringPolicy` and its `version`, which every analysis records as `policy_version`

## Rules

- Hard rule 1: no framework, ORM, SDK, Pydantic or other `app` layer (`llm`, `models`, `repositories`, `services`, `api`).
- Hard rule 4: arithmetic stays exact; rounding happens only in the `present_*` functions of `decimals.py`.
- Hard rule 3: `reconciliation.py` lets the LLM raise a human control, never lower it, and decide a method only where the rules return `NEEDS_REVIEW`.
- Every figure must still come out with the LLM off or failing (`llm_status=unavailable`).
- Unknown inputs stay unknown and are reported; they are never guessed.

## Verify

```bash
uv run pytest tests/unit/domain tests/unit/test_boundaries.py
```
