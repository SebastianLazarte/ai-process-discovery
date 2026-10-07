# ADR 0001: Deterministic-first analysis

**Status:** accepted · 2026-10-07

## Context

The product combines rules and a language model. A model can describe a process well and still return a wrong number, or quietly drop a safeguard the business needs.

## Decision

Everything that can be computed reliably from data, rules or arithmetic lives in `app/domain/` as plain Python: monthly hours, cost, suitability score, method classification, human control, savings, payback and ROI. The LLM only interprets text, proposes methods where the rules return `NEEDS_REVIEW`, and lists risks and dependencies.

Authority order: **system facts > user-confirmed facts > LLM suggestions.** The LLM may raise a human control and can never lower one.

The output schema the model fills (`LLMAnalysisOutput`) has no field for any business number. Telling the model not to compute them is weaker than giving it nowhere to put them.

## Consequences

- The application still calculates hours, costs, scores and ROI with the LLM switched off or failing (`llm_status=unavailable`).
- `domain/` imports no framework; a test enforces it.
- Every analysis records `rules_version` and, when used, `prompt_version`, provider and model, so two results can be explained.

## Alternatives rejected

- **One large prompt that returns everything.** Fast to build, impossible to test and impossible to defend when a figure is wrong.
- **LLM computes, code checks.** Duplicates the work and still leaves the question of which number wins.
