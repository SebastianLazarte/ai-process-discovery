"""Daily usage counters of the public demo (ADR 0020, RS-114).

Routes record an event after their service succeeds. A row holds a UTC day, an event and a
count, nothing that points back to a visitor, so the purge leaves the counters in place.
"""

import logging
from dataclasses import dataclass
from datetime import date, timedelta
from enum import StrEnum

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.models.persistence.base import utcnow
from app.repositories.usage_repository import UsageRepository

logger = logging.getLogger(__name__)


class UsageEvent(StrEnum):
    """What a visitor did, in the order a visit usually goes."""

    DEMO_LOADED = "demo_loaded"
    PROCESS_CREATED = "process_created"
    ANALYSIS_RUN = "analysis_run"
    OVERRIDE_CREATED = "override_created"
    BLUEPRINT_VIEWED = "blueprint_viewed"
    BLUEPRINT_DOWNLOADED = "blueprint_downloaded"


@dataclass(frozen=True)
class UsageDay:
    day: date
    counts: dict[UsageEvent, int]


class UsageService:
    def __init__(self, session: Session) -> None:
        self._session = session
        self._repo = UsageRepository(session)

    def record(self, event: UsageEvent) -> None:
        """Count ``event`` for today (UTC). A failure is logged and never reaches the visitor."""
        try:
            self._repo.increment(utcnow().date(), event.value)
            self._session.commit()
        except SQLAlchemyError:
            self._session.rollback()
            logger.warning("usage_not_recorded", extra={"event": event.value})

    def report(self, days: int, today: date | None = None) -> list[UsageDay]:
        """One entry per UTC day of the last ``days`` days, newest first, 0 for no events."""
        if days < 1:
            raise ValueError("days must be at least 1")
        last = today or utcnow().date()
        first = last - timedelta(days=days - 1)
        stored = {
            (day, event): count for day, event, count in self._repo.counts_between(first, last)
        }
        return [
            UsageDay(
                day=day,
                counts={event: stored.get((day, event.value), 0) for event in UsageEvent},
            )
            for day in (last - timedelta(days=offset) for offset in range(days))
        ]
