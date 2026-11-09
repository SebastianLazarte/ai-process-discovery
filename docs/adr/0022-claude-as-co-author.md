# ADR 0022: Claude as co-author of commits

**Status:** accepted · 2026-11-09 · changes hard rule 8 and RS-102

## Context

Hard rule 8 kept every commit and pull request authored by the maintainer alone and blocked any credit to an AI assistant, in the commit-msg hook and in the `pr-title` job (`scripts/check_ai_credit.py`, RS-102). The maintainer builds this project with Claude and now wants that to show on GitHub, as a collaborator and nothing more: no model name and no tool footer.

## Decision

- **One line.** A commit may carry exactly `Co-Authored-By: Claude <noreply@anthropic.com>`. GitHub shows Claude as a co-author of the commit and among the contributors.
- **Nothing else.** A trailer that names a model, any other line with `noreply@anthropic.com`, and a "Generated with Claude Code" footer stay blocked, in commits and in pull request bodies.
- **Same checks.** `scripts/check_ai_credit.py` allows that exact line and rejects every other form, in the commit-msg hook and in the `pr-title` job. The maintainer's local agent hook follows the same pattern.
- **History stays.** Earlier commits are not rewritten.

## Consequences

- New commits written with Claude show its avatar next to the maintainer's. The squash merge keeps the trailer, since GitHub copies co-authors into the squash commit.
- The maintainer remains the author and the one who merges; release-please releases keep the maintainer's name (ADR 0006).
- The rule now has an allowed form, so the check has one more test per side: the exact line passes, any variant fails.

## Alternatives rejected

| Alternative | Why not |
|---|---|
| A mention in the README | Does not show Claude as a collaborator on the commits |
| Dropping the check | The model name and the tool footer would come back unnoticed |
| Rewriting the history to add the trailer | Rewrites every published commit and tag for no gain |

## How to revert

Restore the earlier `CREDIT` pattern without `ALLOWED` in `scripts/check_ai_credit.py`, its tests and hard rule 8, in a new ADR.
