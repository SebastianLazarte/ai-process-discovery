# ADR 0005: Streamlit as a REST client

**Status:** accepted · 2026-10-07

## Decision

The Streamlit UI calls the FastAPI service over HTTP with `httpx`. It never imports the `app` package, services or the database. A test fails if `ui/` imports `app`.

## Consequences

- The UI can be replaced (React, a CLI, another service) without touching the backend.
- Running the UI needs the API running. `compose.yaml` starts both.
