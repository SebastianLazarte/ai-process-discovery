"""Alembic environment (ADR 0008, RS-59).

The URL comes from ``sqlalchemy.url`` when a caller sets it (the tests do), otherwise from
the application settings, so the CLI and the API always read the same DATABASE_URL.
Migrations run as an operator step before a new version starts, never on API startup.
"""

from logging.config import fileConfig

from alembic import context

from app.core.config import get_settings
from app.core.db import build_engine
from app.models.persistence import Base

config = context.config

# The CLI gets the logging of alembic.ini. Callers inside a running process (the tests)
# set configure_logger to False, so their own logging stays as it is.
if config.config_file_name is not None and config.attributes.get("configure_logger", True):
    fileConfig(config.config_file_name, disable_existing_loggers=False)

target_metadata = Base.metadata


def _database_url() -> str:
    return config.get_main_option("sqlalchemy.url") or get_settings().database_url


def run_migrations_offline() -> None:
    context.configure(
        url=_database_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        render_as_batch=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    engine = build_engine(_database_url())
    try:
        with engine.connect() as connection:
            # Batch mode lets SQLite, which cannot alter most columns in place, run the
            # same migrations as PostgreSQL.
            context.configure(
                connection=connection,
                target_metadata=target_metadata,
                render_as_batch=True,
            )
            with context.begin_transaction():
                context.run_migrations()
    finally:
        engine.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
