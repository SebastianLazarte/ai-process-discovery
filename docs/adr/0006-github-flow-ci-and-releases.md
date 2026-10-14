# ADR 0006: GitHub Flow, required checks and automated releases

**Status:** accepted · 2026-10-07 · required checks amended by ADR 0009

## Decision

**Planning.** Each system requirement in `docs/requirements.toml` is one issue, grouped in a milestone per build block (B0 to B9) and tracked on a GitHub Project board. `scripts/bootstrap_github.py` creates all of it and can be re-run.

**Flow.** One branch per issue, one pull request per change, squash merge only. Pull request titles follow Conventional Commits and are validated in CI, so the history of `main` is readable and release-please can build the changelog from it.

**Protection.** A ruleset on `main` blocks direct pushes and force pushes, requires linear history, resolved conversations and these checks: `quality`, `web`, `test (3.12)`, `test (3.13)`, `test-postgres`, `docker`, `pr-title`. No approval count is required because the project has one maintainer.

**Checks.**

| Job | What it proves |
|---|---|
| `quality` | Formatting, lint and strict typing |
| `web` | The client modules parse and the client tests pass (`node --test`) |
| `test` | Unit and integration tests on SQLite, coverage at least 85 %, on Python 3.12 and 3.13 |
| `test-postgres` | The same integration suite on PostgreSQL 17 |
| `docker` | The image builds and the compose stack becomes healthy |
| `codeql`, `dependency-review` | Static security analysis and vulnerable dependency gate |

**Releases.** release-please keeps a release pull request with the changelog and version bump. Merging it tags `vX.Y.Z`, publishes a GitHub Release and pushes the image to `ghcr.io` with provenance and SBOM. Versions stay `0.x` until the demo is complete.

**Release authorship and approval.** The maintainer signs off every release. release-please runs with the maintainer's `RELEASE_PLEASE_TOKEN`, so the release pull request, its squash commit, the tag and the GitHub Release carry the maintainer's name, and the pull request text is set in `release-please-config.json` instead of the tool's default. GitHub does not let an author approve their own pull request, so the review is recorded as the merge itself. The production deploy (ADR 0008, RS-67) runs in the `production` environment, which requires the maintainer's approval before it starts.

**Supply chain.** Actions are pinned by full commit SHA and updated by Dependabot, together with Python and Docker dependencies.

**Secrets.** The real-LLM contract test runs only by manual dispatch, with the key stored in the `llm` environment, so it never runs on pull requests from forks.

## Consequences

- Nothing reaches `main` without passing the same checks a reviewer would run.
- The release pull request needs `RELEASE_PLEASE_TOKEN`: a fine-grained PAT of the maintainer, limited to this repository, with contents, pull requests and issues write, and an expiry of 90 days. Without it, the PR is created with `GITHUB_TOKEN`: it is attributed to `github-actions[bot]` and the required checks never report. Releases 1.0.0 to 1.2.0 were made that way and stay in the history as they are.
- The token is rotated before it expires. A release run that fails to authenticate is the reminder.
