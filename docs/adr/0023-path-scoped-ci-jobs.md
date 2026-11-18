# ADR 0023: CI runs the slow jobs only when the change can affect them

**Status:** accepted · 2026-11-18 · amends the required checks of ADR 0006 and ADR 0009 (RS-123)

## Context

Every pull request ran the eight jobs of `ci.yml`. A change to Markdown alone built both images, started the stack twice and ran the Playwright walkthroughs, which takes minutes and proves nothing the change could break. The `frontend` job said it "runs on every pull request so it can be required".

All eight checks are required by the ruleset on `main` (`REQUIRED_CHECKS` in `scripts/bootstrap_github.py`). A workflow skipped by a `paths` or `paths-ignore` filter never reports its checks, so the pull request waits for them forever. A job skipped by its own `if:` reports "skipped", which satisfies a required check.

The end-to-end walkthroughs stay useful on a change to the API alone: they cross Nginx, Next.js, FastAPI, the migrations and PostgreSQL, and a route, a status code, a header or a catalog file can break a screen with every Python test green.

## Decision

- **One workflow.** A `changes` job runs `scripts/ci_changes.py` (standard library only) on the files the pull request changes, `git diff base...head`, and outputs three groups. The slow jobs need it and skip with `if:`:

  | Job | Runs on a pull request when a changed file is |
  |---|---|
  | `frontend` | under `frontend/`, or `openapi.json`, or `ci.yml` |
  | `test-postgres` | under `src/` or `tests/integration/`, or `alembic.ini`, `pyproject.toml`, `uv.lock`, `ci.yml` |
  | `docker`, `e2e` | anything but documentation and Python tests |

- **Documentation** is any `*.md`, anything under `docs/` or `.github/ISSUE_TEMPLATE/`, `.github/pr-checklist.toml` and `LICENSE`. `README.md` goes into the API image as package metadata only, so it counts as documentation too.
- **Always run.** `quality`, `test (3.12)`, `test (3.13)` and `pr-title` run on every pull request: pytest reads the README, the `CLAUDE.md` files, the runbook, the backlog and the workflows, and a skipped matrix job reports `test` instead of `test (3.12)`, which would leave the required check waiting.
- **Fail safe.** An unknown file needs the whole stack, and so does an empty diff. A failed or missing classification runs every slow job (`needs.changes.result != 'success'`).
- **`main` runs everything.** A push to `main`, which `release.yml` publishes from, and a manual run (`workflow_dispatch`) skip nothing.
- `changes` is not a required check, and `REQUIRED_CHECKS` does not change.

## Consequences

- A documentation pull request needs `quality`, `test` and `pr-title`, a few minutes instead of the full stack.
- A new kind of file outside the known paths runs the full stack until the script learns about it. That is the safe side.
- The rules live in one tested function (`classify` in `scripts/ci_changes.py`, `tests/unit/test_ci_changes.py`), and a test checks that the slow jobs carry the condition and the fast ones do not.
- A change to `ci.yml` runs every job, so the workflow itself is always tested in full.

## Alternatives rejected

| Alternative | Why not |
|---|---|
| Two workflows, one with `paths-ignore` | The skipped workflow never reports its required checks, so the pull request cannot merge |
| `dorny/paths-filter` | A third-party action for a few lines of Python; one more dependency to pin and update (ADR 0010) |
| Dropping `e2e` from the required checks | A change to the API could then break a screen and merge |
| Skipping `test` on documentation | pytest checks the docs; and a skipped matrix job does not report its required check name |

## How to revert

Remove the `changes` job, the `needs: changes` and `if:` lines of the four slow jobs, `scripts/ci_changes.py` and its test, in a new ADR.
