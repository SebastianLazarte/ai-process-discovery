# ADR 0011: Automated quality gauntlet

**Status:** proposed · 2026-10-15 · amends ADR 0006 (coverage minimum)

## Context

Agents write a growing share of the code in this repository. Robert C. Martin describes not reading the code his agents write and relying instead on a gauntlet of constraints: unit and acceptance tests, coverage, complexity limits, module size, dependency rules and mutation testing. Grady Booch answers that metrics give confidence in behaviour and none about vulnerabilities, dead code or a missed abstraction.

Both points hold. The useful question for this repo is which review work a machine can take over, so that human review spends its time where only a human helps.

The repo already has most of the gauntlet: strict typing, lint, layer boundaries as tests (`tests/unit/test_boundaries.py`), a 98 % branch coverage that CI only required at 85 %, PostgreSQL integration tests, CodeQL and dependency review. Two gaps remained:

- **Nothing measured whether the tests catch bugs.** Coverage says a line ran, not that a test would fail if the line were wrong. A first mutation run on `src/app/domain/` killed 631 of 805 mutants (78 %) despite 98 % coverage. Survivors included hard rule 3 (reconciliation could return no human control) and hard rule 4 (presentation rounding could drop `ROUND_HALF_UP`).
- **Nothing limited complexity.** A function could grow without bound and still pass.

## Decision

- **Mutation testing with mutmut** on `src/app/domain/`, where every business rule lives. A weekly and on-demand workflow (`mutation.yml`) fails below a minimum score, a ratchet that starts at 83 % and only rises. It is not a required check: a run takes minutes, too slow for every pull request.
- **Property-based tests with Hypothesis** for the hard rules and the business case. Generated processes, steps and AI suggestions check invariants that example tests only sample: the AI never lowers a human control, decides a method only where rules return `NEEDS_REVIEW`, hours saved never exceed current hours, and presentation rounds half up.
- **Complexity and size limits in ruff**: McCabe complexity 10, at most 12 branches, 6 returns and 50 statements per function, and 7 arguments until the analysis service is split (RS-84), then 5. The legacy Streamlit client is exempt because it is pending removal.
- **Coverage minimum raised from 85 % to 95 %**, below the current 98 % so a small change does not fail on noise.
- **Refactor only behind a safety net.** Services get characterization tests (RS-82) before any refactor (RS-83 to RS-87), and a refactor keeps those tests unchanged.
- **Human review stays**, focused on what the gauntlet cannot judge: the requirement itself, security, naming and design. The pull request checklist already lists those questions.

## Consequences

- With these changes the domain kills 672 of 805 mutants (83.5 %). Most survivors change a message string; they are reported in the workflow artifact and are worth killing only when the text is part of a contract.
- Hypothesis found that per-step hours add up to the total only to 28 significant digits, the `Decimal` context precision. Presented values are unaffected; the property states the tolerance.
- Two new development dependencies, `mutmut` and `hypothesis`, under the update policy of ADR 0010.
- A rule that a limit flags is fixed or justified in review, never silenced with a blanket ignore.

## Alternatives rejected

| Option | Why not |
|---|---|
| No human review once checks pass | Checks prove behaviour against the tests written; they cannot tell whether the requirement or the threat model was right |
| Mutation testing on every pull request | Minutes per run on one module; the weekly ratchet catches decay at a fraction of the cost |
| Mutation testing on the whole codebase | Routes and repositories are covered by integration tests where most mutants only change wiring; the domain is where a surviving mutant means a wrong number |
| cosmic-ray instead of mutmut | Richer configuration and distributed runs, but a separate session database and more setup for one small module |
| 100 % mutation score | Many survivors only change error text; chasing them produces brittle tests that assert wording |
| CRAP metric | Complexity limits plus 95 % coverage already bound it; a dedicated tool adds little here |

## How to revert

Delete `.github/workflows/mutation.yml`, `scripts/mutation_score.py`, `tests/strategies.py`, `tests/unit/domain/test_properties.py` and `tests/unit/test_mutation_score.py`; remove `mutmut`, `hypothesis`, `[tool.mutmut]` and the `C90`/`PLR09` selection from `pyproject.toml`; set the coverage minimum back.
