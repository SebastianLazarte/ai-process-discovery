"""Embedder factory and its settings (RS-117)."""

import pytest

from app.core.config import Settings
from app.llm.provider import LLMConfigurationError
from app.retrieval.embedders import get_embedder
from app.retrieval.embedders.fake import FakeEmbedder


@pytest.mark.req("RS-117", criterion=4)
def test_the_default_embedding_provider_is_fake(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("EMBEDDING_PROVIDER", raising=False)
    assert Settings(_env_file=None).embedding_provider == "fake"  # type: ignore[call-arg]


@pytest.mark.req("RS-117", criterion=4)
def test_the_default_settings_need_no_voyage_key_and_pick_the_lite_model(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("VOYAGE_API_KEY", raising=False)
    monkeypatch.delenv("VOYAGE_MODEL", raising=False)
    settings = Settings(_env_file=None)  # type: ignore[call-arg]
    assert (settings.voyage_api_key, settings.voyage_model) == (None, "voyage-4-lite")


@pytest.mark.req("RS-117", criterion=4)
def test_the_factory_builds_the_fake_embedder_for_fake() -> None:
    assert isinstance(get_embedder(Settings(embedding_provider="fake")), FakeEmbedder)


def test_the_voyage_provider_is_not_built_yet() -> None:
    with pytest.raises(LLMConfigurationError, match="RS-120"):
        get_embedder(Settings(embedding_provider="voyage"))
