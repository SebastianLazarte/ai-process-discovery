"""Delete public demo data older than the retention window (ADR 0008, RS-63).

    python -m app.purge --older-than-hours 24

On the server a systemd timer runs it inside the API container, just after midnight UTC
(docs/runbook/production.md). No HTTP route calls it.
"""

import argparse
import sys
from datetime import timedelta

from app.core.config import Settings, get_settings
from app.core.db import build_engine, session_factory
from app.core.logging import configure_logging
from app.services.retention_service import RetentionService

DEFAULT_RETENTION_HOURS = 24


def _positive_hours(value: str) -> int:
    hours = int(value)
    if hours < 1:
        raise argparse.ArgumentTypeError("must be at least 1")
    return hours


def main(argv: list[str] | None = None, settings: Settings | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m app.purge",
        description="Delete processes created before the retention window, "
        "with their steps, analyses and overrides.",
    )
    parser.add_argument(
        "--older-than-hours",
        type=_positive_hours,
        default=DEFAULT_RETENTION_HOURS,
        help=f"retention window in hours (default {DEFAULT_RETENTION_HOURS})",
    )
    args = parser.parse_args(argv)

    settings = settings or get_settings()
    configure_logging(settings.log_level)
    engine = build_engine(settings.database_url)
    try:
        with session_factory(engine)() as session:
            RetentionService(session).purge(timedelta(hours=args.older_than_hours))
    finally:
        engine.dispose()
    return 0


if __name__ == "__main__":
    sys.exit(main())
