import json
from importlib import resources
from typing import Any

from fastapi import APIRouter, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.api.dependencies import ProcessServiceDep
from app.core.errors import NotFoundError
from app.models.schemas.process import ProcessCreate, ProcessRead

router = APIRouter(tags=["system"])

DEMO_PACKAGE = "app.demo"


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


@router.get("/demo-processes")
def list_demo_processes() -> list[dict[str, Any]]:
    return [
        {"slug": slug, "name": data["name"], "description": data["description"]}
        for slug, data in _demo_files().items()
    ]


@router.post("/demo-processes/{slug}", status_code=status.HTTP_201_CREATED)
def load_demo_process(slug: str, service: ProcessServiceDep) -> ProcessRead:
    demos = _demo_files()
    if slug not in demos:
        raise NotFoundError(f"demo process {slug!r} not found")
    return service.create(ProcessCreate.model_validate(demos[slug]))


def _demo_files() -> dict[str, dict[str, Any]]:
    folder = resources.files(DEMO_PACKAGE)
    return {
        entry.name.removesuffix(".json"): json.loads(entry.read_text(encoding="utf-8"))
        for entry in sorted(folder.iterdir(), key=lambda e: e.name)
        if entry.name.endswith(".json")
    }
