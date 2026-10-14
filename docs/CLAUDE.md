# Docs: decisions and requirements

Stable reference for the whole repo. Code changes read from here; this folder changes only when a decision or a requirement does.

| Folder or file | Holds |
|---|---|
| `adr/` | Technical decisions |
| `pdr/` | Product and scope decisions |
| `requirements.toml` | User requirements (`RU-nn`) and system requirements (`RS-nn`), one GitHub issue per RS |
| `runbook/` | Operating the production demo |

## Decision index

| Doc | Decision | Status |
|---|---|---|
| PDR 001 | MVP scope; "no hosted deployment" amended by ADR 0008 | accepted |
| ADR 0001 | Python computes every number, the LLM only interprets; authority order | accepted |
| ADR 0002 | SQLite locally, PostgreSQL in CI, `ExactDecimal`, no migrations yet | accepted |
| ADR 0003 | Domain, contracts and persistence are separate models | accepted |
| ADR 0004 | `LLMProvider` protocol, fake by default, Anthropic first, versioned prompt | accepted |
| ADR 0005 | Streamlit as a REST client | replaced by ADR 0007 from 1.2.0; Streamlit pending removal |
| ADR 0006 | GitHub Flow, required checks, release-please, release authorship | accepted; required checks amended by ADR 0009 |
| ADR 0007 | Vanilla web client served by FastAPI | replaced by ADR 0009 from 2.0.0; `web/` pending removal |
| ADR 0008 | Public demo on the maintainer's VPS (block B11, RS-59 to RS-68) | accepted; layout amended by ADR 0009 |
| ADR 0009 | Next.js frontend as a separate service, API under `/api` (block B12, RS-69 to RS-80) | accepted |

Adding or changing a decision updates this index, and the routing table in the root `CLAUDE.md` when it opens a new area.

## When a record is needed

- ADR: a new dependency, a reversed decision, or a change to a hard rule.
- PDR: a change of product scope, audience or non-goals.

## Writing an ADR

- File `adr/NNNN-kebab-title.md` with the next free number.
- Heading `# ADR NNNN: Title`, then `**Status:** accepted · YYYY-MM-DD`, with "replaces" or "amends" when it does.
- Sections: Context, Decision, Consequences, Alternatives rejected; How to revert when useful. Decision first, short.
- An accepted record is never rewritten. A new one replaces or amends it, and the old one gets its status updated.

## requirements.toml

- Each `[[requirement]]` has `id`, `ru`, `block`, `area`, `title` and `acceptance`.
- `tests/unit/test_requirements_file.py` checks that ids are contiguous, each RS traces to a known RU and has acceptance criteria, and `block` is B0 to B11. A new block widens that test.
- `scripts/bootstrap_github.py` turns the file into issues, milestones and the project board, and can be re-run.

## Style

English, hard rule 6 (no em dash, no "it's not X, it's Y"). The runbook uses placeholders (`<domain>`, `<vps>`), never real hosts or secrets.

## Verify

```bash
uv run pytest tests/unit/test_requirements_file.py
```
