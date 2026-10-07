from uuid import UUID

from fastapi import APIRouter, status
from fastapi.responses import PlainTextResponse

from app.api.dependencies import AnalysisServiceDep
from app.models.schemas.analysis import (
    AnalysisCreate,
    AnalysisRead,
    AnalysisSummary,
    Blueprint,
    OverrideCreate,
)
from app.services.blueprint_service import build_blueprint, render_markdown

router = APIRouter(tags=["analyses"])


@router.post(
    "/processes/{process_id}/analyses",
    status_code=status.HTTP_201_CREATED,
    responses={409: {"description": "Sensitive steps need confirm_sensitive=true"}},
)
def create_analysis(
    process_id: UUID, data: AnalysisCreate, service: AnalysisServiceDep
) -> AnalysisRead:
    return service.run(process_id, data)


@router.get("/processes/{process_id}/analyses")
def list_analyses(process_id: UUID, service: AnalysisServiceDep) -> list[AnalysisSummary]:
    return service.list_for_process(process_id)


@router.get("/analyses/{analysis_id}")
def get_analysis(analysis_id: UUID, service: AnalysisServiceDep) -> AnalysisRead:
    return service.get(analysis_id)


@router.post("/analyses/{analysis_id}/overrides", status_code=status.HTTP_201_CREATED)
def create_override(
    analysis_id: UUID, data: OverrideCreate, service: AnalysisServiceDep
) -> AnalysisRead:
    return service.add_override(analysis_id, data)


@router.get("/analyses/{analysis_id}/blueprint")
def get_blueprint(analysis_id: UUID, service: AnalysisServiceDep) -> Blueprint:
    return build_blueprint(service.get(analysis_id), service.get_snapshot(analysis_id))


@router.get("/analyses/{analysis_id}/blueprint.md", response_class=PlainTextResponse)
def get_blueprint_markdown(analysis_id: UUID, service: AnalysisServiceDep) -> PlainTextResponse:
    blueprint = build_blueprint(service.get(analysis_id), service.get_snapshot(analysis_id))
    return PlainTextResponse(render_markdown(blueprint), media_type="text/markdown")
