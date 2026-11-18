"""Text chunks of the sector catalog, each carrying its context (ADR 0021).

A step alone ("Check the data") is ambiguous; with its sector and process in front it is
not. The input is the catalog as ``catalog_files()`` returns it, so this module reads no
file and imports nothing from the services.
"""

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ChunkText:
    process_slug: str
    # 1-based position of the step in its process; None for the chunk of the process itself.
    step_position: int | None
    text: str


def chunk_catalog(catalog: Mapping[str, Mapping[str, Any]]) -> list[ChunkText]:
    """One chunk per process, then one per step, in the order of the files."""
    chunks: list[ChunkText] = []
    for sector in catalog.values():
        for template in sector["templates"]:
            chunks.append(_process_chunk(sector["name"], template))
            chunks.extend(_step_chunks(sector["name"], template))
    return chunks


def _process_chunk(sector_name: str, template: Mapping[str, Any]) -> ChunkText:
    step_names = "; ".join(step["name"] for step in template["steps"])
    description = _sentence(template["description"])
    text = f"{sector_name}. {template['name']}. {description} Steps: {step_names}."
    return ChunkText(process_slug=template["slug"], step_position=None, text=text)


def _step_chunks(sector_name: str, template: Mapping[str, Any]) -> list[ChunkText]:
    return [
        ChunkText(
            process_slug=template["slug"],
            step_position=position,
            text=_step_text(sector_name, template["name"], step),
        )
        for position, step in enumerate(template["steps"], start=1)
    ]


def _step_text(sector_name: str, process_name: str, step: Mapping[str, Any]) -> str:
    text = (
        f"{sector_name}. {process_name}. {step['name']}: {_sentence(step['description'])} "
        f"Role: {step['responsible_role']}."
    )
    tools = step.get("tools") or []
    if tools:
        text += f" Tools: {', '.join(tools)}."
    return text


def _sentence(text: str) -> str:
    return text.rstrip(". ") + "."
