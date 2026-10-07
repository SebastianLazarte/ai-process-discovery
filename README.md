# AI Process Discovery & Automation Planner

[![CI](https://github.com/SebastianLazarte/ai-process-discovery/actions/workflows/ci.yml/badge.svg)](https://github.com/SebastianLazarte/ai-process-discovery/actions/workflows/ci.yml)

Turns a business process described step by step into a quantified, explainable automation blueprint. Code computes every number. The LLM only interprets what is ambiguous, and it cannot remove a human control.

**Status:** under construction, one pull request per build block. Requirements and acceptance criteria live in [docs/requirements.toml](docs/requirements.toml); scope and non-goals in [PDR 001](docs/pdr/001-mvp-scope.md); the delivery process in [ADR 0006](docs/adr/0006-github-flow-ci-and-releases.md) and [CONTRIBUTING](CONTRIBUTING.md).

```bash
uv sync --all-extras
uv run pytest
```
