"""Catalog chunks: one per step and one per process, each with its context (RS-117)."""

from typing import Any

import pytest

from app.retrieval.chunks import ChunkText, chunk_catalog
from app.services.template_service import catalog_files

CATALOG: dict[str, dict[str, Any]] = {
    "insurance": {
        "name": "Insurance",
        "templates": [
            {
                "slug": "claims-intake",
                "name": "Claims intake (first notice of loss)",
                "description": "A policyholder reports a loss.",
                "steps": [
                    {
                        "name": "Receive the first notice of loss",
                        "description": "Take the report of the loss by phone, email or web form",
                        "responsible_role": "Claims Handler",
                        "tools": ["Phone"],
                        "repetitiveness": "HIGH",
                    },
                    {
                        "name": "Check the cover",
                        "description": "Confirm the policy was in force",
                        "responsible_role": "Claims Handler",
                        "tools": ["Policy system", "Claims system"],
                        "repetitiveness": "HIGH",
                    },
                ],
            },
            {
                "slug": "renewal",
                "name": "Policy renewal",
                "description": "A policy comes up for renewal.",
                "steps": [
                    {
                        "name": "Send the offer",
                        "description": "Send the renewal offer",
                        "responsible_role": "Underwriter",
                        "tools": [],
                    }
                ],
            },
        ],
    },
    "logistics": {
        "name": "Logistics",
        "templates": [
            {
                "slug": "dispatch",
                "name": "Dispatch",
                "description": "Orders leave the warehouse.",
                "steps": [
                    {
                        "name": "Pack",
                        "description": "Pack the order",
                        "responsible_role": "Packer",
                        "tools": ["Scanner"],
                    }
                ],
            }
        ],
    },
}


def _step_chunks(chunks: list[ChunkText]) -> list[ChunkText]:
    return [chunk for chunk in chunks if chunk.step_position is not None]


def _process_chunks(chunks: list[ChunkText]) -> list[ChunkText]:
    return [chunk for chunk in chunks if chunk.step_position is None]


@pytest.mark.req("RS-117", criterion=3)
def test_a_step_chunk_starts_with_sector_and_process_then_the_step() -> None:
    first = _step_chunks(chunk_catalog(CATALOG))[0]
    assert first == ChunkText(
        process_slug="claims-intake",
        step_position=1,
        text=(
            "Insurance. Claims intake (first notice of loss). Receive the first notice of loss: "
            "Take the report of the loss by phone, email or web form. "
            "Role: Claims Handler. Tools: Phone."
        ),
    )


@pytest.mark.req("RS-117", criterion=3)
def test_a_step_chunk_lists_every_tool() -> None:
    second = _step_chunks(chunk_catalog(CATALOG))[1]
    assert second.text.endswith("Role: Claims Handler. Tools: Policy system, Claims system.")


@pytest.mark.req("RS-117", criterion=3)
def test_a_step_without_tools_has_no_tools_sentence() -> None:
    renewal = next(c for c in _step_chunks(chunk_catalog(CATALOG)) if c.process_slug == "renewal")
    assert renewal.text == (
        "Insurance. Policy renewal. Send the offer: Send the renewal offer. Role: Underwriter."
    )


@pytest.mark.req("RS-117", criterion=3)
def test_a_description_that_already_ends_with_a_period_gets_no_second_one() -> None:
    catalog = {
        "s": {
            "name": "Sector",
            "templates": [
                {
                    "slug": "p",
                    "name": "Process",
                    "description": "Does things.",
                    "steps": [
                        {
                            "name": "Step",
                            "description": "Do it.",
                            "responsible_role": "Clerk",
                            "tools": [],
                        }
                    ],
                }
            ],
        }
    }
    assert [c.text for c in chunk_catalog(catalog)] == [
        "Sector. Process. Does things. Steps: Step.",
        "Sector. Process. Step: Do it. Role: Clerk.",
    ]


@pytest.mark.req("RS-117", criterion=3)
def test_step_positions_are_one_based_within_their_process() -> None:
    chunks = _step_chunks(chunk_catalog(CATALOG))
    assert [(c.process_slug, c.step_position) for c in chunks] == [
        ("claims-intake", 1),
        ("claims-intake", 2),
        ("renewal", 1),
        ("dispatch", 1),
    ]


@pytest.mark.req("RS-117", criterion=3)
def test_a_process_chunk_holds_sector_name_description_and_step_names() -> None:
    chunk = _process_chunks(chunk_catalog(CATALOG))[0]
    assert chunk == ChunkText(
        process_slug="claims-intake",
        step_position=None,
        text=(
            "Insurance. Claims intake (first notice of loss). A policyholder reports a loss. "
            "Steps: Receive the first notice of loss; Check the cover."
        ),
    )


@pytest.mark.req("RS-117", criterion=3)
def test_there_is_one_process_chunk_per_process() -> None:
    assert [c.process_slug for c in _process_chunks(chunk_catalog(CATALOG))] == [
        "claims-intake",
        "renewal",
        "dispatch",
    ]


@pytest.mark.req("RS-117", criterion=3)
def test_chunks_keep_the_order_of_the_files() -> None:
    chunks = chunk_catalog(CATALOG)
    assert [(c.process_slug, c.step_position) for c in chunks] == [
        ("claims-intake", None),
        ("claims-intake", 1),
        ("claims-intake", 2),
        ("renewal", None),
        ("renewal", 1),
        ("dispatch", None),
        ("dispatch", 1),
    ]


@pytest.mark.req("RS-117", criterion=3)
def test_enum_traits_stay_out_of_the_chunks() -> None:
    assert not any("HIGH" in chunk.text for chunk in chunk_catalog(CATALOG))


@pytest.mark.req("RS-117", criterion=3)
def test_an_empty_catalog_gives_no_chunks() -> None:
    assert chunk_catalog({}) == []


@pytest.mark.req("RS-117", criterion=3)
def test_the_real_catalog_gives_one_process_chunk_for_each_of_its_processes() -> None:
    catalog = catalog_files()
    slugs = [template["slug"] for sector in catalog.values() for template in sector["templates"]]
    chunks = _process_chunks(chunk_catalog(catalog))
    assert slugs
    assert [chunk.process_slug for chunk in chunks] == slugs


@pytest.mark.req("RS-117", criterion=3)
def test_every_step_chunk_of_the_real_catalog_starts_with_its_sector_and_process() -> None:
    catalog = catalog_files()
    prefixes = {
        template["slug"]: f"{sector['name']}. {template['name']}."
        for sector in catalog.values()
        for template in sector["templates"]
    }
    chunks = _step_chunks(chunk_catalog(catalog))
    assert [c for c in chunks if not c.text.startswith(prefixes[c.process_slug])] == []


@pytest.mark.req("RS-117", criterion=3)
def test_the_real_catalog_gives_one_step_chunk_for_each_step() -> None:
    catalog = catalog_files()
    steps = sum(
        len(template["steps"]) for sector in catalog.values() for template in sector["templates"]
    )
    assert len(_step_chunks(chunk_catalog(catalog))) == steps


def test_a_chunk_is_frozen() -> None:
    chunk = ChunkText(process_slug="p", step_position=None, text="t")
    with pytest.raises(AttributeError):
        chunk.text = "other"  # type: ignore[misc]
