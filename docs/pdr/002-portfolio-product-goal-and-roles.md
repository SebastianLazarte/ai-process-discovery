# PDR 002: Product Goal, roles and Scrum backlog

**Status:** accepted · 2026-10-14 · amends PDR 001 (target user)

## Problem

PDR 001 names one target user, an automation consultant or operations lead, and the requirements file lists needs and system requirements without saying who each one serves, how big it is or what comes first. Since ADR 0008 the product is also a public demo with visitors and a person who runs it. Reviewers outside the project need a backlog they can read with standard terms.

## Product Goal

A live, production-grade demo that shows how to build AI-assisted software people can trust: code computes every number, the AI only interprets, and the engineering holds up from backend to frontend to delivery.

## Roles

| Role | Who | Needs |
|---|---|---|
| Operations lead | Owns a business process and its budget | Decide what to automate, with numbers they can defend |
| Demo visitor | Recruiter, hiring manager or engineer | Try the product in minutes, without installing or signing up |
| Maintainer | Builds and runs the demo | Keep cost, data and the shared host safe; ship without manual steps |

The operations lead replaces the automation consultant as the primary user. The workflow of PDR 001 does not change.

## Way of working

- The maintainer is the Product Owner and approves every story.
- The backlog follows Scrum with common agile practice: epics written as user stories, backlog items as user stories or enablers, Given/When/Then criteria, Fibonacci story points, MoSCoW priority with an explicit rank, and releases as milestones.
- Sprints last one week, starting on 2026-10-14. A Definition of Ready and a Definition of Done are kept in `docs/CLAUDE.md`.
- The definition of the backlog lives in `docs/requirements.toml` and changes by pull request. Status and sprint live in GitHub.
- Items delivered before this record keep their original wording as history. Open items are refined before they enter a sprint.

## Success criteria

- Every epic names one of the three roles and reads "As a <role>, I want <what>, so that <why>".
- Every item in a sprint meets the Definition of Ready.
- The board shows points, priority and sprint for open items.

## Non-goals

- No velocity reporting or burndown charts until a few sprints have run.
- No time tracking.
