## What changes

<!-- One or two sentences. The PR title must follow Conventional Commits: `feat(scoring): ...` -->

## Requirements covered

<!-- Requirement IDs from docs/requirements.yaml, e.g. RS-09, RS-10 -->

Closes #

## How it was verified

<!-- Tests added, commands run, manual walkthrough for UI changes -->

## Checklist

- [ ] `uv run pre-commit run --all-files` passes
- [ ] `uv run pytest` passes locally
- [ ] Domain code still imports no framework (FastAPI, SQLAlchemy, SDKs, Streamlit)
- [ ] No LLM-produced value overrides a deterministic fact or removes a human control
- [ ] Docs or ADR updated when a decision or dependency changed
