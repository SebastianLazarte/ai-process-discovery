"""Synthetic demo processes, loaded with a first analysis already run (RS-89).

Each file in `app.demo` holds a process and optional `assumptions`, whose reductions are keyed
by step name because step ids exist only once the process is stored.
"""

import json
from importlib import resources
from typing import Any

from app.core.errors import NotFoundError
from app.models.schemas.analysis import AnalysisCreate, BusinessCaseInput
from app.models.schemas.process import ProcessCreate, ProcessRead
from app.services.analysis_service import AnalysisService
from app.services.process_service import ProcessService

DEMO_PACKAGE = "app.demo"


def demo_files() -> dict[str, dict[str, Any]]:
    folder = resources.files(DEMO_PACKAGE)
    return {
        entry.name.removesuffix(".json"): json.loads(entry.read_text(encoding="utf-8"))
        for entry in sorted(folder.iterdir(), key=lambda e: e.name)
        if entry.name.endswith(".json")
    }


class DemoService:
    def __init__(self, processes: ProcessService, analyses: AnalysisService) -> None:
        self._processes = processes
        self._analyses = analyses

    def list(self) -> list[dict[str, str]]:
        return [
            {"slug": slug, "name": data["name"], "description": data["description"]}
            for slug, data in demo_files().items()
        ]

    def load(self, slug: str) -> ProcessRead:
        """Store the demo process and, when it has assumptions, a first analysis without the LLM."""
        demo = demo_files().get(slug)
        if demo is None:
            raise NotFoundError(f"demo process {slug!r} not found")
        preset = demo.pop("assumptions", None)
        process = self._processes.create(ProcessCreate.model_validate(demo))
        if preset is not None:
            ids = {step.name: step.id for step in process.steps}
            reductions = preset.get("expected_time_reduction_by_step", {})
            assumptions = BusinessCaseInput.model_validate(
                {**preset, "expected_time_reduction_by_step": {ids[n]: v for n, v in reductions.items()}}
            )
            self._analyses.run(process.id, AnalysisCreate(assumptions=assumptions))
        return process
