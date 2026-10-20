# Docs: decisions and requirements

Stable reference for the whole repo. Code changes read from here; this folder changes only when a decision or a requirement does.

| Folder or file | Holds |
|---|---|
| `adr/` | Technical decisions |
| `pdr/` | Product and scope decisions |
| `requirements.toml` | Product backlog: Product Goal, epics (`RU-nn`) and backlog items (`RS-nn`), one GitHub issue per RS |
| `runbook/` | Operating the production demo |
| `design/` | UX and UI specs for the Next.js client, numbered in the order of ADR 0013: brief, discovery, wireframes, foundations, components, usability |

## Decision index

| Doc | Decision | Status |
|---|---|---|
| PDR 001 | MVP scope; "no hosted deployment" amended by ADR 0008 | accepted; target user amended by PDR 002 |
| PDR 002 | Product Goal (portfolio demo), roles and Scrum backlog | accepted |
| ADR 0001 | Python computes every number, the LLM only interprets; authority order | accepted |
| ADR 0002 | SQLite locally, PostgreSQL in CI, `ExactDecimal`, no migrations yet | accepted; migrations amended by ADR 0008 (Alembic from RS-59) |
| ADR 0003 | Domain, contracts and persistence are separate models | accepted |
| ADR 0004 | `LLMProvider` protocol, fake by default, Anthropic first, versioned prompt | accepted |
| ADR 0005 | Streamlit as a REST client | replaced by ADR 0007 from 1.2.0; Streamlit pending removal |
| ADR 0006 | GitHub Flow, required checks, release-please, release authorship | accepted; required checks amended by ADR 0009, supply chain by ADR 0010, coverage minimum by ADR 0011 |
| ADR 0007 | Vanilla web client served by FastAPI | replaced by ADR 0009 from 2.0.0; `web/` pending removal |
| ADR 0008 | Public demo on the maintainer's VPS (block B11, RS-59 to RS-68) | accepted; layout amended by ADR 0009 |
| ADR 0009 | Next.js frontend as a separate service, API under `/api` (block B12, RS-69 to RS-80; RS-91 to RS-94 split from RS-74 to RS-76) | accepted; dependencies amended by ADR 0013 |
| ADR 0010 | Dependency updates: grouped minor and patch after a cooldown, majors planned, Python version fixed | accepted |
| ADR 0011 | Automated quality gauntlet: mutation testing on the domain, property-based tests, complexity limits, coverage 95 % | proposed; completed by ADR 0012 |
| ADR 0012 | Test quality standard: ISO/IEC/IEEE 29119-4 techniques, ISO/IEC 25010 evidence map, marked requirement traceability, LLM eval dataset with task success rate and cost | accepted |
| ADR 0013 | Design system: tokens in CSS as source of truth, light and dark by system setting with a cookie toggle, WCAG 2.2 AA, Penpot and Claude Design as free tools | proposed; navigation and themes amended by ADR 0014 |
| ADR 0014 | Keep the look of the vanilla client: its sidebar and its exact dark palette as tokens, light theme later | accepted |

Adding or changing a decision updates this index, and the routing table in the root `CLAUDE.md` when it opens a new area.

## When a record is needed

- ADR: a new dependency, a reversed decision, or a change to a hard rule.
- PDR: a change of product scope, audience or non-goals.

## Writing an ADR

- File `adr/NNNN-kebab-title.md` with the next free number.
- Heading `# ADR NNNN: Title`, then `**Status:** accepted · YYYY-MM-DD`, with "replaces" or "amends" when it does.
- Sections: Context, Decision, Consequences, Alternatives rejected; How to revert when useful. Decision first, short.
- An accepted record is never rewritten. A new one replaces or amends it, and the old one gets its status updated.

## Scrum (PDR 002)

The maintainer is the Product Owner and writes and approves the stories. An agent may propose a story, criteria or an estimate, marked as a proposal, and never adds one to the file without the Product Owner's approval.

| Scrum | Here |
|---|---|
| Product Goal | `[product] goal` |
| Epic | `[user_requirements.RU-nn]`: `name` and a story (`as_a`, `i_want`, `so_that`) |
| Backlog item | `[[requirement]]` `RS-nn`: a user story or an enabler, one GitHub issue |
| Release | `block` B0 to B13, one milestone each |
| Sprint | One week from `first_sprint`; the Sprint field on the GitHub Project board |

- **Definition of Ready**: a story (`as_a` from `roles`, `i_want`, `so_that`) or an enabler with a clear title; at least one Given/When/Then criterion; `points` in 1, 2, 3, 5 or 8 (split anything larger); `priority` must, should, could or wont; a `rank`; approved by the PO. Only Ready items enter a sprint.
- **Definition of Done**: a pull request with a Conventional Commits title that closes the issue, one test per criterion, required checks green, docs and the area's `CLAUDE.md` up to date, squash merged into `main`.
- Status and sprint live in GitHub (issue state and the Project board), never in the file.

## requirements.toml

- `[product]` holds `goal`, `sprint_days`, `first_sprint` and `roles`.
- Each `[[requirement]]` has `id`, `ru`, `block`, `area` and `title`. A refined item adds `kind`, the story fields when it is a story, `points`, `priority`, `rank` and `[[requirement.criteria]]` with `given`, `when` and `then`. An item delivered before refinement keeps its `acceptance` list instead.
- `tests/unit/test_requirements_file.py` checks contiguous ids, that every item traces to an epic and a release, that each item has either `acceptance` or `criteria`, that refined items meet the Definition of Ready with unique ranks, and that every epic and role is used. A new block widens that test.
- `scripts/bootstrap_github.py` turns the file into issues (epic, story, criteria, priority label), milestones and the Project board with Points and Priority fields, and can be re-run. `--sync` rewrites existing issues to match the file and keeps ticked criteria; run it with `--dry-run` first. The board needs `gh auth refresh -s project`.
- The board's Sprint field is created once by hand: Project settings, New field, Iteration, name `Sprint`, start on the `first_sprint` date, duration 1 week.

## Style

English, hard rule 6 (no em dash, no "it's not X, it's Y"). The runbook uses placeholders (`<domain>`, `<vps>`), never real hosts or secrets.

## Verify

```bash
uv run pytest tests/unit/test_requirements_file.py
```
