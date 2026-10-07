# PDR 001: MVP scope

**Status:** accepted · 2026-10-07

## Problem

Teams that want to automate manual processes decide by intuition. Nobody measures how much time each step takes, which steps are technically suitable, what control a person must keep, or what the business case looks like with honest assumptions.

## Target user

An automation consultant or operations lead who maps a process with the people who run it and needs a defensible recommendation to estimate and build from.

## Core workflow

Describe a process step by step → quantify the current state → deterministic suitability assessment → optional AI enrichment → human review with recorded overrides → automation blueprint.

## In scope

- Processes and ordered steps with the attributes the scoring rules read
- Exact time and cost metrics, including conditional steps
- Versioned scoring policy, method classification and human control
- Business case from user assumptions
- One real LLM provider behind an interface, plus a deterministic fake
- Reconciliation that keeps rules, AI and final recommendations
- Immutable, versioned analyses and human overrides with reasons
- Blueprint in JSON and Markdown
- Streamlit client, Docker image, CI/CD

## Success criteria

- The full flow runs locally with the fake provider and no key
- Removing the LLM leaves hours, costs, scores and ROI unchanged
- Every requirement in `docs/requirements.toml` is closed by a merged pull request with green checks

## Non-goals

- No RAG
- No autonomous agents
- No authentication or enterprise identity
- No multi-tenancy
- No billing
- No automatic n8n workflow generation
- No integrations with real business systems
- No hosted public deployment
