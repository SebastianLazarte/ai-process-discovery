# ADR 0010: Dependency update policy

**Status:** accepted · 2026-10-15 · amends ADR 0006 (supply chain)

## Context

ADR 0006 has Dependabot update GitHub Actions, Python packages and the Docker base image every week, but it says nothing about which updates to take. The first weekly run opened four pull requests at once, and two of them showed the gap:

- `python:3.12-slim` to `python:3.14-slim`. The checks passed only because no job runs the tests on 3.14: the project targets 3.12, CI tests 3.12 and 3.13, and the `docker` job only builds and starts the image.
- The development group used the scope `deps-dev`, which the `pr-title` check rejects, so a harmless ruff update was blocked.

The demo is public and runs the released image, so an update that breaks at runtime reaches visitors.

## Decision

- **Lockfile first.** `uv.lock` pins every Python package; nothing changes between builds unless a pull request changes the lock.
- **Small, regular updates.** Dependabot keeps its weekly run. Minor and patch updates arrive grouped: actions, runtime packages and development packages.
- **Cooldown before adoption.** A release must be public for some days before Dependabot proposes it: 3 days for a patch, 7 for a minor and 30 for a major on Python packages, and 7 days for actions and the Docker image, which do not support per-level cooldowns. Most broken or compromised releases are found and pulled within that window.
- **Majors are planned work.** Each major update arrives alone, outside the groups. It merges only after it enters the backlog as an item, with an ADR when it changes a decision.
- **The Python version is a decision.** Dependabot ignores minor and major updates of the `python` base image. The `3.12-slim` tag still receives Python patch releases on every image build. Moving to a new Python version changes `pyproject.toml`, the CI matrix and the image together, with an ADR.
- **Security updates are not delayed.** Dependabot security updates, enabled by `scripts/bootstrap_github.py` next to vulnerability alerts, skip the cooldown and arrive as soon as an advisory is published.
- **No auto-merge.** The maintainer merges every update once the required checks pass.
- **Titles pass the `pr-title` check.** `deps-dev` joins the allowed scopes.

## Consequences

- Fewer pull requests each week, each one smaller and lower in risk.
- New versions arrive a few days late. That is the intended trade-off.
- A major update can wait open for a while; the backlog makes that waiting visible instead of silent.
- Packages still in 0.x (FastAPI, for example) can break in a minor release; the cooldown and the test suite are the guard for them.

## Alternatives rejected

| Option | Why not |
|---|---|
| Ignore majors entirely | Maximum stability, but the project stops hearing about them and the debt grows into one large jump |
| Auto-merge patches with green checks | Common in large teams; one maintainer reviewing a few grouped pull requests a week does not need another workflow |
| Renovate instead of Dependabot | More options (for example a minimum release age per package), but a new app and configuration for needs Dependabot already covers |
| No cooldown | Adopts releases on the day they ship, when broken or compromised versions are most likely |
