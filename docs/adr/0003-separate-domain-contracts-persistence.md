# ADR 0003: Domain, contracts and persistence are separate models

**Status:** accepted · 2026-10-07

## Decision

| Layer | Technology | Role |
|---|---|---|
| `domain/` | frozen dataclasses | Business behaviour and invariants |
| `models/schemas/` | Pydantic | External contracts: HTTP and OpenAPI |
| `llm/schemas.py` | Pydantic | The contract with the model, input and output |
| `models/persistence/` | SQLAlchemy 2.x | Storage |

Repositories map stored rows to domain objects (`to_domain`), and domain invariants run again on every mapping.

## Consequences

- HTTP contracts can change without touching storage, and the other way round.
- Some fields are declared three times. That is the price of keeping `domain/` free of frameworks, and it is accepted on purpose.
