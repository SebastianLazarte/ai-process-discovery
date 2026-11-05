from fastapi import APIRouter, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy import text

from app import __version__
from app.api.dependencies import DemoServiceDep
from app.models.schemas.process import ProcessRead

router = APIRouter(tags=["system"])


@router.get("/health")
def health(request: Request) -> JSONResponse:
    try:
        with request.app.state.engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        database = "ok"
    except Exception:
        database = "unavailable"
    healthy = database == "ok"
    return JSONResponse(
        {"status": "ok" if healthy else "degraded", "database": database},
        status_code=status.HTTP_200_OK if healthy else status.HTTP_503_SERVICE_UNAVAILABLE,
    )


class AppMeta(BaseModel):
    version: str
    public_demo: bool
    process_drafts_enabled: bool


@router.get("/meta")
def meta(request: Request) -> AppMeta:
    """What the client needs to know about this deployment."""
    settings = request.app.state.settings
    return AppMeta(
        version=__version__,
        public_demo=settings.public_demo,
        process_drafts_enabled=settings.process_drafts_enabled,
    )


class DemoSummary(BaseModel):
    slug: str
    name: str
    description: str
    # The figures a demo card shows (RS-106), counted by the API. None when unknown.
    step_count: int | None = None
    executions_per_month: int | None = None


@router.get("/demo-processes")
def list_demo_processes(service: DemoServiceDep) -> list[DemoSummary]:
    return [DemoSummary(**demo) for demo in service.list()]


@router.post("/demo-processes/{slug}", status_code=status.HTTP_201_CREATED)
def load_demo_process(slug: str, service: DemoServiceDep) -> ProcessRead:
    """Create the demo process, plus a first analysis without the LLM when it has assumptions."""
    return service.load(slug)
