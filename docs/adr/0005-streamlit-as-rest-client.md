# ADR 0005: Streamlit as a REST client

**Status:** accepted · 2026-10-07 · replaced by ADR 0007 from 1.2.0 · retired in 2.0.0, Streamlit removed (RS-80)

## Decision

The Streamlit UI calls the FastAPI service over HTTP with `httpx`. It never imports the `app` package, services or the database. A test fails if `ui/` imports `app`.

## Consequences

- The UI can be replaced (React, a CLI, another service) without touching the backend.
- Running the UI needs the API running. `compose.yaml` starts both.
- From 1.1.0 the web client of [ADR 0007](0007-vanilla-web-client-served-by-fastapi.md) runs next to Streamlit. Streamlit is removed in 1.2.0 and this ADR is then superseded.
