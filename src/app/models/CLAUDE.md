# Models: contracts and persistence

`schemas/` holds the Pydantic HTTP contracts, `persistence/` the SQLAlchemy tables. `repositories/` maps between them and the domain.

## Read

- `docs/adr/0003-separate-domain-contracts-persistence.md`
- `docs/adr/0002-sqlite-locally-postgresql-in-ci.md`

## Rules

- One concept, three models: domain dataclass, Pydantic contract, ORM row. Fields declared three times is the accepted price.
- Repositories map rows with `to_domain`, and domain invariants run again on every mapping.
- Money and hours are stored with `ExactDecimal` (`NUMERIC` on PostgreSQL, text on SQLite), never float.
- The limits in `schemas/process.py` (`MAX_STEPS`, `MAX_SHORT_TEXT`, `MAX_LONG_TEXT`, `MAX_LIST_ITEMS`) also bound the prompt size of the public demo (ADR 0008).
- Analyses are immutable once stored.
- Tables come from `create_all`; there are no migrations yet. ADR 0008 plans Alembic before the first schema change in production (RS-59).

## Verify

```bash
uv run pytest tests/integration
```

The `test-postgres` CI job runs the same suite on PostgreSQL 17.
