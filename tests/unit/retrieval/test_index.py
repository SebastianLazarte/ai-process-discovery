"""The catalog index: built with an embedder, saved with a hash, refused when stale (RS-118)."""

import copy
import json
from collections.abc import Sequence
from pathlib import Path
from typing import Any

import pytest

from app.domain.retrieval import CatalogChunk
from app.llm.provider import LLMConfigurationError
from app.retrieval.chunks import chunk_catalog
from app.retrieval.embedder import InputType
from app.retrieval.embedders.fake import FakeEmbedder
from app.retrieval.index import (
    CatalogIndex,
    build_index,
    catalog_hash,
    index_folder,
    index_path,
    load_index,
    save_index,
)
from app.services.template_service import catalog_files

CATALOG: dict[str, dict[str, Any]] = {
    "insurance": {
        "name": "Insurance",
        "templates": [
            {
                "slug": "claims-intake",
                "name": "Claims intake",
                "description": "A policyholder reports a loss.",
                "steps": [
                    {
                        "name": "Receive the notice",
                        "description": "Take the report by phone",
                        "responsible_role": "Claims Handler",
                    },
                    {
                        "name": "Check the cover",
                        "description": "Confirm the policy was in force",
                        "responsible_role": "Claims Handler",
                        "tools": ["Policy system"],
                    },
                ],
            }
        ],
    }
}


class SpyEmbedder:
    """Records every call and answers with a vector that tells the texts apart."""

    name = "spy"
    model = "spy-model-1"

    def __init__(self) -> None:
        self.calls: list[tuple[list[str], InputType]] = []

    def embed(self, texts: Sequence[str], input_type: InputType) -> list[tuple[float, ...]]:
        self.calls.append((list(texts), input_type))
        return [(1.0, float(position)) for position, _ in enumerate(texts)]


def _stale_files(folder: Path, catalog: dict[str, dict[str, Any]]) -> list[str]:
    """Messages for every index file in ``folder`` that ``load_index`` refuses."""
    problems: list[str] = []
    for path in sorted(folder.glob("*.json")):
        try:
            load_index(path, catalog)
        except LLMConfigurationError as error:
            problems.append(str(error))
    return problems


@pytest.mark.req("RS-118", criterion=1)
def test_the_hash_is_a_sha256_hex_digest() -> None:
    assert len(catalog_hash(CATALOG)) == 64


@pytest.mark.req("RS-118", criterion=1)
def test_the_hash_ignores_the_order_of_keys() -> None:
    reordered = {"insurance": dict(reversed(list(CATALOG["insurance"].items())))}
    assert catalog_hash(reordered) == catalog_hash(CATALOG)


@pytest.mark.req("RS-118", criterion=1)
def test_the_hash_ignores_how_the_files_are_formatted() -> None:
    text = json.dumps(CATALOG, indent=4, ensure_ascii=False).replace("\n", "\r\n")
    assert catalog_hash(json.loads(text)) == catalog_hash(CATALOG)


@pytest.mark.req("RS-118", criterion=1)
def test_the_hash_changes_when_a_word_of_the_catalog_changes() -> None:
    edited = copy.deepcopy(CATALOG)
    edited["insurance"]["templates"][0]["steps"][0]["description"] = "Take the report by email"
    assert catalog_hash(edited) != catalog_hash(CATALOG)


@pytest.mark.req("RS-118", criterion=1)
def test_the_hash_keeps_accents_as_they_are() -> None:
    accented = {"s": {"name": "Reclamación"}}
    assert catalog_hash(accented) != catalog_hash({"s": {"name": "Reclamacion"}})


@pytest.mark.req("RS-118", criterion=1)
def test_building_embeds_every_chunk_text_once_as_document() -> None:
    spy = SpyEmbedder()
    build_index(spy, CATALOG)
    assert spy.calls == [([chunk.text for chunk in chunk_catalog(CATALOG)], "document")]


@pytest.mark.req("RS-118", criterion=1)
def test_building_pairs_each_vector_with_its_process_and_step() -> None:
    index = build_index(SpyEmbedder(), CATALOG)
    assert index.chunks == (
        CatalogChunk("claims-intake", None, (1.0, 0.0)),
        CatalogChunk("claims-intake", 1, (1.0, 1.0)),
        CatalogChunk("claims-intake", 2, (1.0, 2.0)),
    )


@pytest.mark.req("RS-118", criterion=1)
def test_building_records_the_model_and_the_hash_of_the_catalog() -> None:
    index = build_index(SpyEmbedder(), CATALOG)
    assert (index.model, index.catalog_hash) == ("spy-model-1", catalog_hash(CATALOG))


@pytest.mark.req("RS-118", criterion=1)
def test_building_refuses_an_embedder_that_returns_a_vector_per_text_short() -> None:
    class Short(SpyEmbedder):
        def embed(self, texts: Sequence[str], input_type: InputType) -> list[tuple[float, ...]]:
            return [(1.0,)]

    with pytest.raises(LLMConfigurationError, match="3 chunks"):
        build_index(Short(), CATALOG)


@pytest.mark.req("RS-118", criterion=1)
def test_a_saved_index_loads_back_equal(tmp_path: Path) -> None:
    index = build_index(FakeEmbedder(), CATALOG)
    save_index(index, tmp_path / "index.json")
    assert load_index(tmp_path / "index.json", CATALOG) == index


@pytest.mark.req("RS-118", criterion=1)
def test_a_saved_index_is_json_with_the_model_the_hash_and_the_vectors(tmp_path: Path) -> None:
    save_index(build_index(SpyEmbedder(), CATALOG), tmp_path / "index.json")
    stored = json.loads((tmp_path / "index.json").read_text(encoding="utf-8"))
    assert stored == {
        "model": "spy-model-1",
        "catalog_hash": catalog_hash(CATALOG),
        "chunks": [
            {"process_slug": "claims-intake", "step_position": None, "vector": [1.0, 0.0]},
            {"process_slug": "claims-intake", "step_position": 1, "vector": [1.0, 1.0]},
            {"process_slug": "claims-intake", "step_position": 2, "vector": [1.0, 2.0]},
        ],
    }


@pytest.mark.req("RS-118", criterion=1)
def test_saving_creates_the_folder_of_the_index(tmp_path: Path) -> None:
    target = tmp_path / "new" / "folder" / "index.json"
    save_index(build_index(SpyEmbedder(), CATALOG), target)
    assert target.is_file()


@pytest.mark.req("RS-118", criterion=1)
def test_the_index_of_a_model_lives_in_the_index_folder_of_the_catalog() -> None:
    path = index_path("voyage-4-lite")
    assert (path.name, path.parent) == ("voyage-4-lite.json", index_folder())


@pytest.mark.req("RS-118", criterion=1)
def test_the_index_folder_sits_inside_the_catalog_package() -> None:
    assert index_folder().parent.name == "catalog"


@pytest.mark.req("RS-118", criterion=1)
@pytest.mark.parametrize("model", ["", "../secrets", "a/b", "a\\b", "x.json"])
def test_a_model_name_that_is_not_a_plain_file_name_has_no_index_path(model: str) -> None:
    with pytest.raises(LLMConfigurationError, match="model name"):
        index_path(model)


@pytest.mark.req("RS-118", criterion=2)
def test_loading_a_stale_index_fails_and_names_the_file(tmp_path: Path) -> None:
    save_index(build_index(SpyEmbedder(), CATALOG), tmp_path / "spy-model-1.json")
    edited = copy.deepcopy(CATALOG)
    edited["insurance"]["name"] = "Insurance and more"
    with pytest.raises(LLMConfigurationError, match=r"spy-model-1\.json.*stale"):
        load_index(tmp_path / "spy-model-1.json", edited)


@pytest.mark.req("RS-118", criterion=2)
def test_the_error_of_a_stale_index_says_how_to_rebuild_it(tmp_path: Path) -> None:
    save_index(build_index(SpyEmbedder(), CATALOG), tmp_path / "i.json")
    with pytest.raises(LLMConfigurationError, match=r"scripts/build_catalog_index\.py"):
        load_index(tmp_path / "i.json", {})


@pytest.mark.req("RS-118", criterion=2)
def test_the_check_of_the_committed_indexes_names_a_stale_file(tmp_path: Path) -> None:
    save_index(build_index(SpyEmbedder(), CATALOG), tmp_path / "old-model.json")
    edited = copy.deepcopy(CATALOG)
    edited["insurance"]["templates"][0]["name"] = "Claims"
    problems = _stale_files(tmp_path, edited)
    assert len(problems) == 1
    assert "old-model.json" in problems[0]


@pytest.mark.req("RS-118", criterion=2)
def test_the_check_of_the_committed_indexes_passes_a_fresh_file(tmp_path: Path) -> None:
    save_index(build_index(SpyEmbedder(), CATALOG), tmp_path / "fresh.json")
    assert _stale_files(tmp_path, CATALOG) == []


@pytest.mark.req("RS-118", criterion=2)
def test_every_committed_index_matches_the_catalog_files() -> None:
    folder = Path(str(index_folder()))
    assert _stale_files(folder, catalog_files()) == []


@pytest.mark.req("RS-118", criterion=2)
def test_loading_a_missing_index_names_the_file_and_the_script(tmp_path: Path) -> None:
    with pytest.raises(LLMConfigurationError, match=r"gone\.json.*build_catalog_index"):
        load_index(tmp_path / "gone.json", CATALOG)


@pytest.mark.req("RS-118", criterion=2)
@pytest.mark.parametrize(
    "content",
    [
        "not json",
        "[]",
        '{"model": "m"}',
        '{"model": "m", "catalog_hash": "h", "chunks": [{"process_slug": "a"}]}',
        '{"model": 1, "catalog_hash": "h", "chunks": []}',
    ],
)
def test_loading_a_file_that_is_not_an_index_names_the_file(tmp_path: Path, content: str) -> None:
    (tmp_path / "broken.json").write_text(content, encoding="utf-8")
    with pytest.raises(LLMConfigurationError, match=r"broken\.json"):
        load_index(tmp_path / "broken.json", CATALOG)


@pytest.mark.req("RS-118", criterion=2)
def test_loading_an_index_with_a_right_hash_and_broken_chunks_names_the_file(
    tmp_path: Path,
) -> None:
    broken = {"model": "m", "catalog_hash": catalog_hash(CATALOG), "chunks": [{"vector": [1]}]}
    (tmp_path / "chunks.json").write_text(json.dumps(broken), encoding="utf-8")
    with pytest.raises(LLMConfigurationError, match=r"chunks\.json.*not an index"):
        load_index(tmp_path / "chunks.json", CATALOG)


@pytest.mark.req("RS-118", criterion=2)
def test_a_wrong_hash_is_reported_as_stale_before_the_chunks_are_read(tmp_path: Path) -> None:
    (tmp_path / "wrong.json").write_text(
        json.dumps({"model": "m", "catalog_hash": "0", "chunks": "garbage"}), encoding="utf-8"
    )
    with pytest.raises(LLMConfigurationError, match="stale"):
        load_index(tmp_path / "wrong.json", CATALOG)


def test_the_index_is_frozen() -> None:
    index = CatalogIndex(model="m", catalog_hash="h", chunks=())
    with pytest.raises(AttributeError):
        index.model = "other"  # type: ignore[misc]
