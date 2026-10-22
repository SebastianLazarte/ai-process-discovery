# Contributing

## Flow

1. Pick an issue. Each one is a requirement (`RS-nn`) with acceptance criteria.
2. Branch from `main`: `feat/rs-12-process-score`, `fix/...`, `docs/...`, `ci/...`.
3. Open a pull request using the template. Title in Conventional Commits, for example `feat(scoring): weight process score by time`. The squash commit takes this title, and release-please builds the changelog from it. A bot comments a checklist for the areas the change touches, with verification questions for its type; it is a guide, not a required check. Add or change items in `.github/pr-checklist.toml`.
4. All required checks must pass: `quality`, `frontend`, `test (3.12)`, `test (3.13)`, `test-postgres`, `docker`, `e2e`, `pr-title`.
5. Squash merge. The branch is deleted automatically.

Types: `feat`, `fix`, `docs`, `test`, `refactor`, `perf`, `ci`, `build`, `chore`. A `feat` bumps the minor version, a `fix` bumps the patch.

## Local checks

```bash
uv sync --all-extras
uv run pre-commit install        # once; installs the pre-commit and commit-msg hooks
uv run pre-commit run --all-files
uv run pytest
cd frontend && corepack pnpm install && corepack pnpm lint && corepack pnpm format && corepack pnpm typecheck && corepack pnpm test && corepack pnpm build && cd ..   # Node 22
uv run mutmut run                 # optional, minutes: mutation testing of the domain
```

CI enforces 95 % branch coverage and ruff's complexity limits on every pull request, and a minimum mutation score on the domain every week ([ADR 0011](docs/adr/0011-automated-quality-gauntlet.md)). A surviving mutant in business logic means a missing test: `uv run mutmut results` lists them and `uv run mutmut show <name>` shows the change.

`tests/integration/test_analysis_snapshot.py` freezes the full analysis, review and blueprint of each demo process. A refactor leaves it untouched; a change of behaviour regenerates it with `UPDATE_SNAPSHOTS=1` and the snapshot diff goes into the pull request for review.

## Rules

- `app/domain/` stays free of frameworks, ORMs, SDKs and Pydantic.
- No value produced by the LLM may overwrite a deterministic fact or remove a human control.
- A new dependency or a reversed decision comes with an ADR in `docs/adr/`.
- Never log prompts or step descriptions.
- `CLAUDE.md` files are agent instructions: a pull request that changes one is reviewed like code, and its branch is never run with an agent before that review.
