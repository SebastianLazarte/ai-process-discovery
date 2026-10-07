from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.domain.entities import Process, ProcessStep
from app.domain.enums import InputType, IntegrationReadiness, Level
from app.models.persistence import ProcessORM, ProcessStepORM


class ProcessRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, process: ProcessORM) -> None:
        self._session.add(process)

    def get(self, process_id: UUID) -> ProcessORM | None:
        return self._session.scalar(
            select(ProcessORM)
            .where(ProcessORM.id == process_id)
            .options(selectinload(ProcessORM.steps))
        )

    def get_step(self, step_id: UUID) -> ProcessStepORM | None:
        return self._session.get(ProcessStepORM, step_id)

    def list(self) -> list[tuple[ProcessORM, int]]:
        step_count = (
            select(func.count(ProcessStepORM.id))
            .where(ProcessStepORM.process_id == ProcessORM.id)
            .scalar_subquery()
        )
        rows = self._session.execute(
            select(ProcessORM, step_count).order_by(ProcessORM.updated_at.desc())
        ).all()
        return [(row[0], int(row[1])) for row in rows]

    def delete(self, process: ProcessORM) -> None:
        self._session.delete(process)


def to_domain(process: ProcessORM) -> Process:
    """Map a stored process to the domain model. Domain invariants run here again."""
    return Process(
        id=process.id,
        name=process.name,
        description=process.description,
        owner=process.owner,
        executions_per_month=process.executions_per_month,
        hourly_cost=process.hourly_cost,
        steps=tuple(_step_to_domain(step) for step in process.steps),
    )


def _step_to_domain(step: ProcessStepORM) -> ProcessStep:
    return ProcessStep(
        id=step.id,
        position=step.position,
        name=step.name,
        description=step.description,
        responsible_role=step.responsible_role,
        tools=tuple(step.tools),
        input_description=step.input_description,
        output_description=step.output_description,
        minutes_per_execution=step.minutes_per_execution,
        occurrence_rate=step.occurrence_rate,
        repetitiveness=Level(step.repetitiveness),
        rule_clarity=Level(step.rule_clarity),
        input_type=InputType(step.input_type),
        exception_rate=step.exception_rate,
        integration_readiness=IntegrationReadiness(step.integration_readiness),
        requires_human_judgement=step.requires_human_judgement,
        requires_human_approval=step.requires_human_approval,
        handles_sensitive_data=step.handles_sensitive_data,
        criticality=Level(step.criticality),
        problems=tuple(step.problems),
    )
