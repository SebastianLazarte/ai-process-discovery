# ADR 0006: GitHub Flow, required checks and automated releases

**Status:** accepted · 2026-10-07

## Decision

**Planning.** Each system requirement in `docs/requirements.toml` is one issue, grouped in a milestone per build block (B0 to B9) and tracked on a GitHub Project board. `scripts/bootstrap_github.py` creates all of it and can be re-run.

**Flow.** One branch per issue, one pull request per change, squash merge only. Pull request titles follow Conventional Commits and are validated in CI, so the history of `main` is readable and release-please can build the changelog from it.

**Protection.** A ruleset on `main` blocks direct pushes and force pushes, requires linear history, resolved conversations and these checks: `quality`, `test (3.12)`, `test (3.13)`, `test-postgres`, `docker`, `pr-title`. No approval count is required because the project has one maintainer.

**Checks.**

| Job | What it proves |
|---|---|
| `quality` | Formatting, lint and strict typing |
| `test` | Unit and integration tests on SQLite, coverage at least 85 %, on Python 3.12 and 3.13 |
| `test-postgres` | The same integration suite on PostgreSQL 17 |
| `docker` | The image builds and the compose stack becomes healthy |
| `codeql`, `dependency-review` | Static security analysis and vulnerable dependency gate |

**Releases.** release-please keeps a release pull request with the changelog and version bump. Merging it tags `vX.Y.Z`, publishes a GitHub Release and pushes the image to `ghcr.io` with provenance and SBOM. Versions stay `0.x` until the demo is complete.

**Supply chain.** Actions are pinned by full commit SHA and updated by Dependabot, together with Python and Docker dependencies.

**Secrets.** The real-LLM contract test runs only by manual dispatch, with the key stored in the `llm` environment, so it never runs on pull requests from forks.

## Consequences

- Nothing reaches `main` without passing the same checks a reviewer would run.
- The release pull request needs `RELEASE_PLEASE_TOKEN` (fine-grained PAT, contents and pull requests write) so its checks run. Without it, the PR is created with `GITHUB_TOKEN` and the required checks never report.
