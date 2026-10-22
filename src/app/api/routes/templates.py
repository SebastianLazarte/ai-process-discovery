from fastapi import APIRouter

from app.api.dependencies import TemplateServiceDep
from app.models.schemas.template import SectorTemplates

router = APIRouter(tags=["templates"])


@router.get("/process-templates")
def list_process_templates(service: TemplateServiceDep) -> list[SectorTemplates]:
    """Common processes grouped by sector, with qualitative step traits and no numbers."""
    return service.list()
