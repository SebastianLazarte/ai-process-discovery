"""Process templates grouped by sector, read from `app.catalog` without any LLM (RS-95).

Each file in `app.catalog` is one sector, named by its id, with its name and templates.
"""

import json
from importlib import resources
from typing import Any

from app.models.schemas.template import SectorTemplates

CATALOG_PACKAGE = "app.catalog"


def catalog_files() -> dict[str, dict[str, Any]]:
    folder = resources.files(CATALOG_PACKAGE)
    return {
        entry.name.removesuffix(".json"): json.loads(entry.read_text(encoding="utf-8"))
        for entry in sorted(folder.iterdir(), key=lambda e: e.name)
        if entry.name.endswith(".json")
    }


class TemplateService:
    def list(self) -> list[SectorTemplates]:
        return [
            SectorTemplates.model_validate({"id": sector_id, **data})
            for sector_id, data in catalog_files().items()
        ]
