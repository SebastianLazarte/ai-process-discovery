"""The catalog index: one vector per chunk, tied to the catalog it was built from (ADR 0021).

An index file holds the model, a hash of the catalog and the vectors. The hash covers the
parsed content of the catalog files, so line endings and formatting never change it and a
changed word always does. ``load_index`` refuses a file whose hash differs from the catalog
it is given, so a catalog change without a rebuilt index never goes unnoticed.
"""

import hashlib
import json
from collections.abc import Mapping
from dataclasses import dataclass
from importlib import resources
from pathlib import Path
from typing import Any

from app.domain.retrieval import CatalogChunk
from app.llm.provider import LLMConfigurationError
from app.retrieval.chunks import chunk_catalog
from app.retrieval.embedder import Embedder

CATALOG_PACKAGE = "app.catalog"
INDEX_FOLDER = "index"
REBUILD_HINT = "Rebuild it with `uv run python scripts/build_catalog_index.py`."

Catalog = Mapping[str, Mapping[str, Any]]


@dataclass(frozen=True)
class CatalogIndex:
    model: str
    catalog_hash: str
    chunks: tuple[CatalogChunk, ...]


def catalog_hash(catalog: Catalog) -> str:
    """SHA-256 of a canonical dump of the catalog, independent of how the files are written."""
    canonical = json.dumps(catalog, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def index_folder() -> Path:
    """``src/app/catalog/index``, next to the sector files and apart from ``catalog_files()``."""
    return Path(str(resources.files(CATALOG_PACKAGE) / INDEX_FOLDER))


def index_path(model: str) -> Path:
    """The file that holds the index of an embedding model."""
    if not model or any(mark in model for mark in "/\\") or model.endswith(".json"):
        raise LLMConfigurationError(f"{model!r} is not a model name that can name an index file")
    return index_folder() / f"{model}.json"


def build_index(embedder: Embedder, catalog: Catalog) -> CatalogIndex:
    """Embed every chunk of the catalog, in one call, as ``document``."""
    chunks = chunk_catalog(catalog)
    vectors = embedder.embed([chunk.text for chunk in chunks], "document")
    if len(vectors) != len(chunks):
        raise LLMConfigurationError(
            f"the embedder returned {len(vectors)} vectors for {len(chunks)} chunks"
        )
    return CatalogIndex(
        model=embedder.model,
        catalog_hash=catalog_hash(catalog),
        chunks=tuple(
            CatalogChunk(chunk.process_slug, chunk.step_position, vector)
            for chunk, vector in zip(chunks, vectors, strict=True)
        ),
    )


def save_index(index: CatalogIndex, path: Path) -> None:
    payload = {
        "model": index.model,
        "catalog_hash": index.catalog_hash,
        "chunks": [
            {
                "process_slug": chunk.process_slug,
                "step_position": chunk.step_position,
                "vector": list(chunk.vector),
            }
            for chunk in index.chunks
        ],
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")


def _not_an_index(path: Path) -> LLMConfigurationError:
    return LLMConfigurationError(f"catalog index {path} is not an index file. {REBUILD_HINT}")


def load_index(path: Path, catalog: Catalog) -> CatalogIndex:
    """Read an index file, provided it was built from exactly this catalog."""
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as error:
        raise LLMConfigurationError(
            f"catalog index {path} cannot be read. {REBUILD_HINT}"
        ) from error
    try:
        stored = json.loads(text)
        model, stored_hash = stored["model"], stored["catalog_hash"]
        if not isinstance(model, str) or not isinstance(stored_hash, str):
            raise TypeError("model and catalog_hash must be text")
    except (ValueError, KeyError, TypeError) as error:
        raise _not_an_index(path) from error
    if stored_hash != catalog_hash(catalog):
        raise LLMConfigurationError(
            f"catalog index {path} is stale: the catalog files changed since it was built. "
            f"{REBUILD_HINT}"
        )
    try:
        chunks = tuple(
            CatalogChunk(
                process_slug=str(item["process_slug"]),
                step_position=item["step_position"],
                vector=tuple(float(value) for value in item["vector"]),
            )
            for item in stored["chunks"]
        )
    except (KeyError, TypeError, ValueError) as error:
        raise _not_an_index(path) from error
    return CatalogIndex(model=model, catalog_hash=stored_hash, chunks=chunks)
