from datetime import date

from sqlalchemy import select
from sqlalchemy.dialects import postgresql, sqlite
from sqlalchemy.orm import Session

from app.models.persistence import UsageCounterORM


class UsageRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def increment(self, day: date, event: str) -> None:
        """Add one to the counter of ``event`` on ``day`` in a single upsert.

        ``INSERT ... ON CONFLICT DO UPDATE`` keeps concurrent requests from losing a count,
        on SQLite and PostgreSQL alike (ADR 0020).
        """
        dialect = self._session.get_bind().dialect.name
        insert = postgresql.insert if dialect == "postgresql" else sqlite.insert
        statement = insert(UsageCounterORM).values(day=day, event=event, count=1)
        self._session.execute(
            statement.on_conflict_do_update(
                index_elements=[UsageCounterORM.day, UsageCounterORM.event],
                set_={"count": UsageCounterORM.count + 1},
            )
        )

    def counts_between(self, first: date, last: date) -> list[tuple[date, str, int]]:
        rows = self._session.execute(
            select(UsageCounterORM.day, UsageCounterORM.event, UsageCounterORM.count).where(
                UsageCounterORM.day >= first, UsageCounterORM.day <= last
            )
        ).all()
        return [(day, event, count) for day, event, count in rows]
