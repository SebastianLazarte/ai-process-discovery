"""scripts/build_catalog_index.py writes the index of the catalog for a model (RS-118)."""

import json
from collections.abc import Sequence
from pathlib import Path

import pytest
from scripts.build_catalog_index import main, write_catalog_index

from app.core.config import Settings
from app.llm.provider import LLMConfigurationError
from app.retrieval.chunks import chunk_catalog
from app.retrieval.embedder import InputType
from app.retrieval.embedders.fake import FakeEmbedder
from app.retrieval.index import catalog_hash, load_index
from app.services.template_service import catalog_files


class StubEmbedder:
    name = "stub"
    model = "stub-model-9"

    def __init__(self) -> None:
        self.calls: list[tuple[int, InputType]] = []

    def embed(self, texts: Sequence[str], input_type: InputType) -> list[tuple[float, ...]]:
        self.calls.append((len(texts), input_type))
        return [(1.0, 0.0) for _ in texts]


@pytest.mark.req("RS-118", criterion=1)
def test_the_script_embeds_the_whole_catalog_in_one_call_as_document(tmp_path: Path) -> None:
    stub = StubEmbedder()
    write_catalog_index(stub, tmp_path / "index.json")
    assert stub.calls == [(len(chunk_catalog(catalog_files())), "document")]


@pytest.mark.req("RS-118", criterion=1)
def test_the_script_writes_the_vectors_and_the_hash_of_the_catalog(tmp_path: Path) -> None:
    target = tmp_path / "stub-model-9.json"
    write_catalog_index(StubEmbedder(), target)
    stored = json.loads(target.read_text(encoding="utf-8"))
    assert (stored["model"], stored["catalog_hash"], len(stored["chunks"])) == (
        "stub-model-9",
        catalog_hash(catalog_files()),
        len(chunk_catalog(catalog_files())),
    )


@pytest.mark.req("RS-118", criterion=1)
def test_the_file_the_script_writes_loads_against_the_catalog(tmp_path: Path) -> None:
    target = tmp_path / "stub-model-9.json"
    index = write_catalog_index(StubEmbedder(), target)
    assert load_index(target, catalog_files()) == index


@pytest.mark.req("RS-118", criterion=1)
def test_the_script_writes_to_the_index_folder_of_the_model_by_default(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    target = tmp_path / "stub-model-9.json"
    monkeypatch.setattr(
        "scripts.build_catalog_index.index_path", lambda model: tmp_path / f"{model}.json"
    )
    assert main(StubEmbedder()) == 0
    assert target.is_file()
    assert "stub-model-9.json" in capsys.readouterr().out


@pytest.mark.req("RS-118", criterion=3)
def test_the_script_refuses_the_fake_embedder_because_its_index_is_never_a_file(
    tmp_path: Path,
) -> None:
    with pytest.raises(LLMConfigurationError, match="built at startup"):
        write_catalog_index(FakeEmbedder(), tmp_path / "fake.json")
    assert list(tmp_path.iterdir()) == []


@pytest.mark.req("RS-118", criterion=3)
def test_the_command_reports_the_fake_refusal_and_exits_with_an_error(
    capsys: pytest.CaptureFixture[str],
) -> None:
    assert main(FakeEmbedder()) == 1
    assert "built at startup" in capsys.readouterr().err


def test_the_command_builds_its_embedder_from_the_settings_when_none_is_given(
    capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        "scripts.build_catalog_index.get_settings", lambda: Settings(embedding_provider="fake")
    )
    assert main() == 1
    assert "built at startup" in capsys.readouterr().err
