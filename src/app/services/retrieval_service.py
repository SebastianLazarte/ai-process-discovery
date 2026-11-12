"""Retrieval of the catalog processes closest to a description (RS-118, ADR 0021).

The service embeds the description, as ``query``, and ranks it against the catalog index
with the pure rules of ``app.domain.retrieval``. It holds no repository and writes nothing:
a description is never stored, indexed or logged, since it can contain personal or
financial data. Logs carry the model and a count, nothing else.
"""

import logging
from typing import Any

from app.core.config import Settings
from app.domain.retrieval import RetrievedProcess, rank_processes
from app.llm.provider import LLMConfigurationError
from app.retrieval.embedder import Embedder
from app.retrieval.embedders import get_embedder
from app.retrieval.index import Catalog, CatalogIndex, build_index, index_path, load_index
from app.services.template_service import catalog_files

logger = logging.getLogger(__name__)


class RetrievalService:
    def __init__(self, embedder: Embedder, index: CatalogIndex, threshold: float) -> None:
        if index.model != embedder.model:
            raise LLMConfigurationError(
                f"the catalog index was built with {index.model} but the embedder is "
                f"{embedder.model}; an index is only read with the model that built it"
            )
        self._embedder = embedder
        self.index = index
        self.threshold = threshold

    def retrieve(self, description: str) -> tuple[RetrievedProcess, ...]:
        (query,) = self._embedder.embed([description], "query")
        found = rank_processes(query, self.index.chunks, threshold=self.threshold)
        extra: dict[str, Any] = {"embedding_model": self._embedder.model, "retrieved": len(found)}
        logger.info("retrieval_done", extra=extra)
        return found


def build_retrieval_service(settings: Settings, catalog: Catalog | None = None) -> RetrievalService:
    """The service for the configured embedder.

    The fake embedder costs nothing, so its index is built in memory and no file is read or
    written. Any other embedder reads the file of its model, which must match the catalog.
    """
    catalog = catalog_files() if catalog is None else catalog
    embedder = get_embedder(settings)
    if embedder.name == "fake":
        index = build_index(embedder, catalog)
    else:
        index = load_index(index_path(embedder.model), catalog)
    logger.info(
        "retrieval_ready",
        extra={"embedding_model": embedder.model, "chunks": len(index.chunks)},
    )
    return RetrievalService(embedder, index, settings.retrieval_threshold)
