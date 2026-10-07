from uuid import UUID

from fastapi import APIRouter, status

from app.api.dependencies import ProcessServiceDep
from app.models.schemas.process import (
    ProcessCreate,
    ProcessRead,
    ProcessSummary,
    ProcessUpdate,
    StepCreate,
    StepOrder,
    StepUpdate,
)

router = APIRouter(tags=["processes"])


@router.post("/processes", status_code=status.HTTP_201_CREATED)
def create_process(data: ProcessCreate, service: ProcessServiceDep) -> ProcessRead:
    return service.create(data)


@router.get("/processes")
def list_processes(service: ProcessServiceDep) -> list[ProcessSummary]:
    return service.list()


@router.get("/processes/{process_id}")
def get_process(process_id: UUID, service: ProcessServiceDep) -> ProcessRead:
    return service.get(process_id)


@router.patch("/processes/{process_id}")
def update_process(
    process_id: UUID, data: ProcessUpdate, service: ProcessServiceDep
) -> ProcessRead:
    return service.update(process_id, data)


@router.delete("/processes/{process_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_process(process_id: UUID, service: ProcessServiceDep) -> None:
    service.delete(process_id)


@router.post("/processes/{process_id}/steps", status_code=status.HTTP_201_CREATED)
def add_step(process_id: UUID, data: StepCreate, service: ProcessServiceDep) -> ProcessRead:
    return service.add_step(process_id, data)


@router.put("/processes/{process_id}/steps/order")
def reorder_steps(process_id: UUID, data: StepOrder, service: ProcessServiceDep) -> ProcessRead:
    return service.reorder_steps(process_id, data)


@router.patch("/steps/{step_id}")
def update_step(step_id: UUID, data: StepUpdate, service: ProcessServiceDep) -> ProcessRead:
    return service.update_step(step_id, data)


@router.delete("/steps/{step_id}")
def delete_step(step_id: UUID, service: ProcessServiceDep) -> ProcessRead:
    return service.delete_step(step_id)
