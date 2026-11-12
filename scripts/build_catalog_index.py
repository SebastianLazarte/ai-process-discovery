"""Write the index of the sector catalog for the configured embedding model (RS-118, ADR 0021).

The index holds one vector per catalog chunk, embedded as `document`, and a hash of the
catalog files. A test fails when the hash no longer matches, so run this after any change
to a file in `src/app/catalog/` and commit the result:

    uv run python scripts/build_catalog_index.py

The fake embedder has no index file: its index is built in memory at startup.
"""

import sys
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from app.core.config import get_settings
from app.llm.provider import LLMConfigurationError, LLMProviderError
from app.retrieval.embedder import Embedder
from app.retrieval.embedders import get_embedder
from app.retrieval.index import CatalogIndex, build_index, index_path, save_index
from app.services.template_service import catalog_files


def write_catalog_index(
    embedder: Embedder, path: Path, catalog: Mapping[str, Mapping[str, Any]] | None = None
) -> CatalogIndex:
    """Embed the catalog with ``embedder`` and write the index to ``path``."""
    if embedder.name == "fake":
        raise LLMConfigurationError(
            "the fake embedder has no index file: its index is built at startup. "
            "Set EMBEDDING_PROVIDER to a real provider to build one."
        )
    index = build_index(embedder, catalog_files() if catalog is None else catalog)
    save_index(index, path)
    return index


def main(embedder: Embedder | None = None, path: Path | None = None) -> int:
    try:
        embedder = embedder or get_embedder(get_settings())
        target = path or index_path(embedder.model)
        index = write_catalog_index(embedder, target)
    except LLMProviderError as error:
        sys.stderr.write(f"{error}\n")
        return 1
    sys.stdout.write(f"Wrote {target} with {len(index.chunks)} chunks for {index.model}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
