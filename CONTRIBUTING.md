# Contributing

## Flow

1. Pick an issue. Each one is a requirement (`RS-nn`) with acceptance criteria.
2. Branch from `main`: `feat/rs-12-process-score`, `fix/...`, `docs/...`, `ci/...`.
3. Open a pull request using the template. Title in Conventional Commits, for example `feat(scoring): weight process score by time`. The squash commit takes this title, and release-please builds the changelog from it.
4. All required checks must pass: `quality`, `test (3.12)`, `test (3.13)`, `test-postgres`, `docker`, `pr-title`.
5. Squash merge. The branch is deleted automatically.

Types: `feat`, `fix`, `docs`, `test`, `refactor`, `perf`, `ci`, `build`, `chore`. A `feat` bumps the minor version, a `fix` bumps the patch.

## Local checks

```bash
uv sync --all-extras
uv run pre-commit install        # once
uv run pre-commit run --all-files
uv run pytest
```

## Rules

- `app/domain/` stays free of frameworks, ORMs, SDKs and Pydantic.
- No value produced by the LLM may overwrite a deterministic fact or remove a human control.
- A new dependency or a reversed decision comes with an ADR in `docs/adr/`.
- Never log prompts or step descriptions.
