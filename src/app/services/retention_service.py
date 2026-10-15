"""Retention of public demo data (ADR 0008, RS-63).

Called only by the purge command (`python -m app.purge`), never by an HTTP route: deleting
data is an operator action, and a request must not be able to trigger it.
"""

import logging
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.models.persistence.base import utcnow
from app.repositories.process_repository import ProcessRepository

logger = logging.getLogger(__name__)


class RetentionService:
    def __init__(self, session: Session) -> None:
        self._session = session
        self._repo = ProcessRepository(session)

    def purge(self, retention: timedelta, now: datetime | None = None) -> int:
        """Delete processes created more than ``retention`` ago, with everything they own.

        The age counts from creation, so editing a process never extends its life.
        """
        if retention <= timedelta(0):
            raise ValueError("retention must be positive")
        cutoff = (now or utcnow()) - retention
        deleted = self._repo.delete_created_before(cutoff)
        self._session.commit()
        logger.info("demo_data_purged", extra={"processes": deleted, "cutoff": cutoff.isoformat()})
        return deleted
