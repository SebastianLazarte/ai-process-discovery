from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.persistence import AnalysisORM, OverrideORM


class AnalysisRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, analysis: AnalysisORM) -> None:
        self._session.add(analysis)

    def get(self, analysis_id: UUID) -> AnalysisORM | None:
        return self._session.scalar(
            select(AnalysisORM)
            .where(AnalysisORM.id == analysis_id)
            .options(selectinload(AnalysisORM.overrides))
        )

    def list_for_process(self, process_id: UUID) -> list[AnalysisORM]:
        return list(
            self._session.scalars(
                select(AnalysisORM)
                .where(AnalysisORM.process_id == process_id)
                .options(selectinload(AnalysisORM.overrides))
                .order_by(AnalysisORM.created_at.desc())
            )
        )

    def add_override(self, override: OverrideORM) -> None:
        self._session.add(override)
