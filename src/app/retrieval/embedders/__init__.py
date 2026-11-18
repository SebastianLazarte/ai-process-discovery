from app.core.config import Settings
from app.llm.provider import LLMConfigurationError
from app.retrieval.embedder import Embedder
from app.retrieval.embedders.fake import FakeEmbedder


def get_embedder(settings: Settings) -> Embedder:
    if settings.embedding_provider == "voyage":
        raise LLMConfigurationError(
            "embedding_provider=voyage is not available yet: the Voyage embedder arrives "
            "with RS-120. Use embedding_provider=fake."
        )
    return FakeEmbedder()
