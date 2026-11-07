from uuid import UUID

from fastapi import APIRouter, status
from fastapi.responses import PlainTextResponse

from app.api.dependencies import AnalysisServiceDep, UsageServiceDep
from app.models.schemas.analysis import (
    AnalysisCreate,
    AnalysisRead,
    AnalysisSummary,
    Blueprint,
    OverrideCreate,
)
from app.services.blueprint_service import build_blueprint, render_markdown
from app.services.usage_service import UsageEvent

router = APIRouter(tags=["analyses"])


@router.post(
    "/processes/{process_id}/analyses",
    status_code=status.HTTP_201_CREATED,
    responses={409: {"description": "Sensitive steps need confirm_sensitive=true"}},
)
def create_analysis(
    process_id: UUID, data: AnalysisCreate, service: AnalysisServiceDep, usage: UsageServiceDep
) -> AnalysisRead:
    analysis = service.run(process_id, data)
    usage.record(UsageEvent.ANALYSIS_RUN)
    return analysis


@router.get("/processes/{process_id}/analyses")
def list_analyses(process_id: UUID, service: AnalysisServiceDep) -> list[AnalysisSummary]:
    return service.list_for_process(process_id)


@router.get("/analyses/{analysis_id}")
def get_analysis(analysis_id: UUID, service: AnalysisServiceDep) -> AnalysisRead:
    return service.get(analysis_id)


@router.post("/analyses/{analysis_id}/overrides", status_code=status.HTTP_201_CREATED)
def create_override(
    analysis_id: UUID, data: OverrideCreate, service: AnalysisServiceDep, usage: UsageServiceDep
) -> AnalysisRead:
    analysis = service.add_override(analysis_id, data)
    usage.record(UsageEvent.OVERRIDE_CREATED)
    return analysis


@router.get("/analyses/{analysis_id}/blueprint")
def get_blueprint(
    analysis_id: UUID, service: AnalysisServiceDep, usage: UsageServiceDep
) -> Blueprint:
    blueprint = build_blueprint(service.get(analysis_id), service.get_snapshot(analysis_id))
    usage.record(UsageEvent.BLUEPRINT_VIEWED)
    return blueprint


@router.get("/analyses/{analysis_id}/blueprint.md", response_class=PlainTextResponse)
def get_blueprint_markdown(
    analysis_id: UUID, service: AnalysisServiceDep, usage: UsageServiceDep
) -> PlainTextResponse:
    blueprint = build_blueprint(service.get(analysis_id), service.get_snapshot(analysis_id))
    usage.record(UsageEvent.BLUEPRINT_DOWNLOADED)
    return PlainTextResponse(render_markdown(blueprint), media_type="text/markdown")
