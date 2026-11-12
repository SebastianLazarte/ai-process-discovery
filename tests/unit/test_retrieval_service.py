"""RetrievalService: embeds only the description and ranks the catalog index (RS-118)."""

import ast
import logging
from collections.abc import Iterator, Sequence
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

import app.services.retrieval_service as service_module
from app.core.config import Settings
from app.domain.retrieval import rank_processes
from app.llm.provider import LLMConfigurationError
from app.main import create_app
from app.retrieval.embedder import InputType
from app.retrieval.embedders.fake import FakeEmbedder
from app.retrieval.index import CatalogIndex, build_index, save_index
from app.services.template_service import catalog_files

CATALOG = catalog_files()
THRESHOLD = 0.6
SECRET = "Zebra quartz unicorn invoice with account 4929-1234"


class SpyEmbedder:
    """The fake embedder, remembering every call it gets."""

    name = "spy"

    def __init__(self) -> None:
        self._inner = FakeEmbedder()
        self.calls: list[tuple[list[str], InputType]] = []

    @property
    def model(self) -> str:
        return self._inner.model

    def embed(self, texts: Sequence[str], input_type: InputType) -> list[tuple[float, ...]]:
        self.calls.append((list(texts), input_type))
        return self._inner.embed(texts, input_type)


@pytest.fixture(scope="module")
def index() -> CatalogIndex:
    return build_index(FakeEmbedder(), CATALOG)


@pytest.fixture
def app_logs(caplog: pytest.LogCaptureFixture) -> Iterator[pytest.LogCaptureFixture]:
    """Capture the app loggers even when ``configure_logging`` stopped them propagating."""
    logger = logging.getLogger("app")
    logger.addHandler(caplog.handler)
    caplog.set_level(logging.DEBUG, logger="app")
    yield caplog
    logger.removeHandler(caplog.handler)


def _first_process() -> dict[str, Any]:
    sector = next(iter(CATALOG.values()))
    template: dict[str, Any] = sector["templates"][0]
    return template


@pytest.mark.req("RS-118", criterion=4)
def test_retrieval_embeds_only_the_description_in_one_call_as_query(index: CatalogIndex) -> None:
    spy = SpyEmbedder()
    service_module.RetrievalService(spy, index, THRESHOLD).retrieve("Check the policy")
    assert spy.calls == [(["Check the policy"], "query")]


@pytest.mark.req("RS-118", criterion=4)
def test_retrieval_returns_the_ranking_of_the_domain_over_the_index(index: CatalogIndex) -> None:
    description = _first_process()["name"] + ". " + _first_process()["description"]
    query = FakeEmbedder().embed([description], "query")[0]
    expected = rank_processes(query, index.chunks, threshold=THRESHOLD)
    assert (
        service_module.RetrievalService(FakeEmbedder(), index, THRESHOLD).retrieve(description)
        == expected
    )


@pytest.mark.req("RS-118", criterion=4)
def test_retrieval_drops_a_description_that_resembles_no_process(index: CatalogIndex) -> None:
    assert (
        service_module.RetrievalService(FakeEmbedder(), index, THRESHOLD).retrieve(
            "Banana smoothie"
        )
        == ()
    )


@pytest.mark.req("RS-118", criterion=4)
def test_a_lower_threshold_keeps_more_of_the_ranking(index: CatalogIndex) -> None:
    strict = service_module.RetrievalService(FakeEmbedder(), index, 0.99).retrieve(
        "Banana smoothie"
    )
    loose = service_module.RetrievalService(FakeEmbedder(), index, 0.0).retrieve("Banana smoothie")
    assert (len(strict), len(loose)) == (0, 3)


@pytest.mark.req("RS-118", criterion=4)
def test_an_index_of_another_model_is_refused(index: CatalogIndex) -> None:
    other = CatalogIndex(
        model="another-model", catalog_hash=index.catalog_hash, chunks=index.chunks
    )
    with pytest.raises(LLMConfigurationError, match="another-model"):
        service_module.RetrievalService(FakeEmbedder(), other, THRESHOLD)


@pytest.mark.req("RS-118", criterion=4)
def test_a_description_that_reuses_the_words_of_a_process_retrieves_it_first(
    index: CatalogIndex,
) -> None:
    template = _first_process()
    description = f"{template['name']}: {template['description']}"
    found = service_module.RetrievalService(FakeEmbedder(), index, THRESHOLD).retrieve(description)
    assert found[0].process_slug == template["slug"]


@pytest.mark.req("RS-118", criterion=4)
def test_every_process_of_the_catalog_is_first_for_its_own_words(index: CatalogIndex) -> None:
    service = service_module.RetrievalService(FakeEmbedder(), index, THRESHOLD)
    templates = [t for sector in CATALOG.values() for t in sector["templates"]]
    first = {
        t["slug"]: service.retrieve(f"{t['name']}. {t['description']}")[0].process_slug
        for t in templates
    }
    assert first == {t["slug"]: t["slug"] for t in templates}


@pytest.mark.req("RS-118", criterion=5)
def test_the_description_is_never_logged(
    index: CatalogIndex, app_logs: pytest.LogCaptureFixture
) -> None:
    service_module.RetrievalService(FakeEmbedder(), index, THRESHOLD).retrieve(SECRET)
    carried = [
        str(value)
        for record in app_logs.records
        for value in (record.getMessage(), *record.__dict__.values())
    ]
    assert [text for text in carried if "unicorn" in text] == []


@pytest.mark.req("RS-118", criterion=5)
def test_retrieval_logs_the_model_and_a_count(
    index: CatalogIndex, app_logs: pytest.LogCaptureFixture
) -> None:
    service_module.RetrievalService(FakeEmbedder(), index, 0.0).retrieve(SECRET)
    record = next(r for r in app_logs.records if r.getMessage() == "retrieval_done")
    assert (record.__dict__["embedding_model"], record.__dict__["retrieved"]) == (
        FakeEmbedder().model,
        3,
    )


@pytest.mark.req("RS-118", criterion=5)
def test_the_description_is_not_added_to_the_index(index: CatalogIndex) -> None:
    before = CatalogIndex(index.model, index.catalog_hash, tuple(index.chunks))
    service_module.RetrievalService(FakeEmbedder(), index, THRESHOLD).retrieve(SECRET)
    assert index == before


@pytest.mark.req("RS-118", criterion=5)
def test_retrieval_writes_no_file(
    index: CatalogIndex, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    service_module.RetrievalService(FakeEmbedder(), index, THRESHOLD).retrieve(SECRET)
    assert list(tmp_path.iterdir()) == []


@pytest.mark.req("RS-118", criterion=5)
def test_the_service_imports_no_repository_nor_orm() -> None:
    tree = ast.parse(Path(service_module.__file__ or "").read_text(encoding="utf-8"))
    modules = {
        name
        for node in ast.walk(tree)
        for name in (
            [alias.name for alias in node.names]
            if isinstance(node, ast.Import)
            else [node.module or ""]
            if isinstance(node, ast.ImportFrom)
            else []
        )
    }
    forbidden = ("app.repositories", "app.models", "sqlalchemy", "fastapi")
    assert [m for m in modules if m.startswith(forbidden)] == []


@pytest.mark.req("RS-118", criterion=3)
def test_with_the_fake_embedder_the_index_is_built_in_memory_and_no_file_is_touched(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def forbidden(*_: object, **__: object) -> None:
        raise AssertionError("the fake index never goes through a file")

    monkeypatch.setattr(service_module, "load_index", forbidden)
    monkeypatch.setattr("app.retrieval.index.save_index", forbidden)
    service = service_module.build_retrieval_service(Settings(embedding_provider="fake"), CATALOG)
    assert service.retrieve("Check the policy and the cover of the claim") is not None


@pytest.mark.req("RS-118", criterion=3)
def test_the_fake_index_has_the_chunks_of_the_catalog(index: CatalogIndex) -> None:
    service = service_module.build_retrieval_service(Settings(embedding_provider="fake"), CATALOG)
    assert service.index == index


@pytest.mark.req("RS-118", criterion=3)
def test_the_app_builds_the_retrieval_service_when_it_starts() -> None:
    settings = Settings(database_url="sqlite://", log_level="WARNING")
    with TestClient(create_app(settings)) as client:
        started = client.app.state.retrieval_service  # type: ignore[attr-defined]
    assert isinstance(started, service_module.RetrievalService)


@pytest.mark.req("RS-118", criterion=1)
def test_with_another_provider_the_index_is_loaded_from_the_file_of_the_model(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    built = build_index(FakeEmbedder(), CATALOG)
    save_index(built, tmp_path / "file.json")
    monkeypatch.setattr(service_module, "get_embedder", lambda settings: SpyEmbedder())
    monkeypatch.setattr(service_module, "index_path", lambda model: tmp_path / "file.json")
    service = service_module.build_retrieval_service(Settings(embedding_provider="voyage"), CATALOG)
    assert service.index == built


@pytest.mark.req("RS-118", criterion=2)
def test_with_another_provider_a_stale_file_stops_the_start_and_names_itself(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    save_index(build_index(FakeEmbedder(), CATALOG), tmp_path / "stale.json")
    monkeypatch.setattr(service_module, "get_embedder", lambda settings: SpyEmbedder())
    monkeypatch.setattr(service_module, "index_path", lambda model: tmp_path / "stale.json")
    with pytest.raises(LLMConfigurationError, match=r"stale\.json"):
        service_module.build_retrieval_service(Settings(embedding_provider="voyage"), {})


@pytest.mark.req("RS-118", criterion=4)
def test_the_threshold_comes_from_the_settings() -> None:
    service = service_module.build_retrieval_service(
        Settings(embedding_provider="fake", retrieval_threshold=0.123), CATALOG
    )
    assert service.threshold == 0.123


@pytest.mark.req("RS-118", criterion=4)
def test_the_default_threshold_keeps_a_process_and_drops_an_unrelated_sentence() -> None:
    settings = Settings(embedding_provider="fake")
    service = service_module.build_retrieval_service(settings, CATALOG)
    template = _first_process()
    kept = service.retrieve(f"{template['name']}. {template['description']}")
    dropped = service.retrieve("What is the weather like on the moon during a football game")
    assert (len(kept) > 0, dropped) == (True, ())
