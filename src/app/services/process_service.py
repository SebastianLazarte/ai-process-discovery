from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.errors import AppError, LimitExceededError, NotFoundError
from app.domain.enums import ExceptionFrequency, StepFrequency
from app.domain.policies import DEFAULT_CAPTURE_POLICY
from app.models.persistence import ProcessORM, ProcessStepORM
from app.models.persistence.base import utcnow
from app.models.schemas.process import (
    MAX_STEPS,
    ProcessCreate,
    ProcessRead,
    ProcessSummary,
    ProcessUpdate,
    StepCreate,
    StepFields,
    StepOrder,
    StepUpdate,
)
from app.repositories.process_repository import ProcessRepository, to_domain


class ProcessService:
    def __init__(self, session: Session) -> None:
        self._session = session
        self._repo = ProcessRepository(session)

    def create(self, data: ProcessCreate) -> ProcessRead:
        process = ProcessORM(**data.model_dump(exclude={"steps"}), version=1)
        process.steps = [
            _new_step(step, position) for position, step in enumerate(data.steps, start=1)
        ]
        to_domain(process)  # enforce domain invariants before saving
        self._repo.add(process)
        self._session.commit()
        return ProcessRead.model_validate(process)

    def list(self) -> list[ProcessSummary]:
        return [
            ProcessSummary(
                id=process.id,
                name=process.name,
                owner=process.owner,
                executions_per_month=process.executions_per_month,
                step_count=count,
                version=process.version,
                updated_at=process.updated_at,
            )
            for process, count in self._repo.list()
        ]

    def get(self, process_id: UUID) -> ProcessRead:
        return ProcessRead.model_validate(self._get(process_id))

    def update(self, process_id: UUID, data: ProcessUpdate) -> ProcessRead:
        process = self._get(process_id)
        for field, value in data.model_dump(exclude_unset=True).items():
            if field != "hourly_cost" and value is None:
                raise AppError(f"{field} cannot be null")
            setattr(process, field, value)
        return self._save(process)

    def delete(self, process_id: UUID) -> None:
        self._repo.delete(self._get(process_id))
        self._session.commit()

    def add_step(self, process_id: UUID, data: StepCreate) -> ProcessRead:
        process = self._get(process_id)
        if len(process.steps) >= MAX_STEPS:
            raise LimitExceededError(f"a process has at most {MAX_STEPS} steps")
        position = data.position or len(process.steps) + 1
        position = min(position, len(process.steps) + 1)
        for step in process.steps:
            if step.position >= position:
                step.position += 1
        process.steps.append(_new_step(data, position))
        process.steps.sort(key=lambda s: s.position)
        return self._save(process)

    def update_step(self, step_id: UUID, data: StepUpdate) -> ProcessRead:
        step = self._get_step(step_id)
        values = data.model_dump(exclude_unset=True)
        for field, value in values.items():
            if field != "exception_rate" and value is None:
                raise AppError(f"{field} cannot be null")
        for field, value in _with_rates(values, creating=False).items():
            setattr(step, field, value.value if hasattr(value, "value") else value)
        return self._save(step.process)

    def delete_step(self, step_id: UUID) -> ProcessRead:
        step = self._get_step(step_id)
        process = step.process
        process.steps.remove(step)
        for position, remaining in enumerate(process.steps, start=1):
            remaining.position = position
        return self._save(process)

    def reorder_steps(self, process_id: UUID, data: StepOrder) -> ProcessRead:
        process = self._get(process_id)
        by_id = {step.id: step for step in process.steps}
        if len(data.step_ids) != len(by_id) or set(data.step_ids) != set(by_id):
            raise AppError("step_ids must list every step of the process exactly once")
        for position, step_id in enumerate(data.step_ids, start=1):
            by_id[step_id].position = position
        process.steps.sort(key=lambda s: s.position)
        return self._save(process)

    def _save(self, process: ProcessORM) -> ProcessRead:
        to_domain(process)
        process.version += 1
        process.updated_at = utcnow()
        self._session.commit()
        self._session.refresh(process)
        return ProcessRead.model_validate(process)

    def _get(self, process_id: UUID) -> ProcessORM:
        process = self._repo.get(process_id)
        if process is None:
            raise NotFoundError(f"process {process_id} not found")
        return process

    def _get_step(self, step_id: UUID) -> ProcessStepORM:
        step = self._repo.get_step(step_id)
        if step is None:
            raise NotFoundError(f"step {step_id} not found")
        return step


def _new_step(data: StepFields, position: int) -> ProcessStepORM:
    given = data.model_dump(mode="python", exclude={"position"}, exclude_unset=True)
    values = data.model_dump(mode="python", exclude={"position"})
    values.update(_with_rates(given, creating=True))
    for key, value in values.items():
        if hasattr(value, "value"):
            values[key] = value.value
    return ProcessStepORM(**values, position=position)


def _with_rates(given: dict[str, Any], *, creating: bool) -> dict[str, Any]:
    """Resolve each plain-word choice and its rate from the fields the client sent (RS-115).

    A choice sets its rate through the capture policy. A rate sent alone is an exact figure
    and clears the choice, except an unknown exception rate, which is the same as "Don't
    know". A new step that sends neither gets the choice its default rate stands for.
    """
    values = dict(given)
    policy = DEFAULT_CAPTURE_POLICY
    if (frequency := given.get("frequency")) is not None:
        values["occurrence_rate"] = policy.occurrence_rate(StepFrequency(frequency))
    elif given.get("occurrence_rate") is not None:
        values["frequency"] = None
    elif creating:
        values["frequency"] = StepFrequency.ALWAYS
        values["occurrence_rate"] = policy.occurrence_rate(StepFrequency.ALWAYS)

    if (exceptions := given.get("exception_frequency")) is not None:
        values["exception_rate"] = policy.exception_rate(ExceptionFrequency(exceptions))
    elif given.get("exception_rate") is not None:
        values["exception_frequency"] = None
    elif creating or "exception_rate" in given:
        values["exception_frequency"] = ExceptionFrequency.UNKNOWN
    return values
