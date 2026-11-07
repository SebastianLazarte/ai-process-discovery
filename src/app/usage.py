"""Print the daily usage counters of the demo (ADR 0020, RS-114).

    python -m app.usage --days 30

On the server it runs inside the API container (docs/runbook/production.md). No HTTP route
exposes the counters.
"""

import argparse
import sys
from collections.abc import Sequence

from app.core.config import Settings, get_settings
from app.core.db import build_engine, session_factory
from app.core.logging import configure_logging
from app.services.usage_service import UsageDay, UsageEvent, UsageService

DEFAULT_DAYS = 30


def _positive_days(value: str) -> int:
    days = int(value)
    if days < 1:
        raise argparse.ArgumentTypeError("must be at least 1")
    return days


def render(report: Sequence[UsageDay]) -> str:
    """A plain text table: one row per day, one column per event, then a total row."""
    header = ["day", *(event.value for event in UsageEvent)]
    rows = [
        [entry.day.isoformat(), *(str(entry.counts[e]) for e in UsageEvent)] for entry in report
    ]
    totals = [sum(entry.counts[event] for entry in report) for event in UsageEvent]
    rows.append(["total", *(str(total) for total in totals)])
    widths = [max(len(row[i]) for row in [header, *rows]) for i in range(len(header))]
    lines = [
        "  ".join(
            cell.ljust(width) if i == 0 else cell.rjust(width)
            for i, (cell, width) in enumerate(zip(row, widths, strict=True))
        )
        for row in [header, *rows]
    ]
    return "\n".join(lines)


def main(argv: list[str] | None = None, settings: Settings | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m app.usage",
        description="Print how many times each event happened on each UTC day.",
    )
    parser.add_argument(
        "--days",
        type=_positive_days,
        default=DEFAULT_DAYS,
        help=f"number of days back from today, today included (default {DEFAULT_DAYS})",
    )
    args = parser.parse_args(argv)

    settings = settings or get_settings()
    configure_logging(settings.log_level)
    engine = build_engine(settings.database_url)
    try:
        with session_factory(engine)() as session:
            report = UsageService(session).report(args.days)
    finally:
        engine.dispose()
    sys.stdout.write(f"{render(report)}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
