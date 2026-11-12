"""Ranking of catalog processes against a description (ADR 0021).

Pure and deterministic: the same query and the same chunks give the same result, in
whatever order the chunks arrive. Similarity is a float; it never touches money or hours.
"""

import math
from collections.abc import Sequence
from dataclasses import dataclass

from app.domain.errors import DomainValidationError


@dataclass(frozen=True)
class CatalogChunk:
    """One embedded text of the catalog: a step with its context, or a whole process."""

    process_slug: str
    step_position: int | None  # 1-based; None for the process-level chunk
    vector: tuple[float, ...]  # normalised


@dataclass(frozen=True)
class StepMatch:
    step_position: int
    similarity: float


@dataclass(frozen=True)
class RetrievedProcess:
    process_slug: str
    similarity: float  # best similarity among its chunks
    steps: tuple[StepMatch, ...]  # its step chunks at or above the threshold, best first


def rank_processes(
    query: Sequence[float],
    chunks: Sequence[CatalogChunk],
    *,
    threshold: float,
    max_processes: int = 3,
    max_steps: int = 3,
) -> tuple[RetrievedProcess, ...]:
    """Return the processes closest to the query, best first.

    A chunk scores as the dot product of its vector and the query (cosine, since both are
    normalised). A process scores as its best chunk and is kept at or above ``threshold``.
    Ties break by slug, and between steps by position.
    """
    if max_processes < 0:
        raise DomainValidationError("max_processes", "must not be negative")
    if max_steps < 0:
        raise DomainValidationError("max_steps", "must not be negative")

    best: dict[str, float] = {}
    matches: dict[str, list[StepMatch]] = {}
    for chunk in chunks:
        if len(chunk.vector) != len(query):
            raise DomainValidationError(
                "vector",
                f"has {len(chunk.vector)} dimensions, the query has {len(query)}",
            )
        similarity = math.sumprod(query, chunk.vector)
        best[chunk.process_slug] = max(best.get(chunk.process_slug, similarity), similarity)
        if chunk.step_position is not None and similarity >= threshold:
            matches.setdefault(chunk.process_slug, []).append(
                StepMatch(chunk.step_position, similarity)
            )

    kept = sorted(
        (slug for slug, score in best.items() if score >= threshold),
        key=lambda slug: (-best[slug], slug),
    )
    return tuple(
        RetrievedProcess(
            process_slug=slug,
            similarity=best[slug],
            steps=tuple(
                sorted(matches.get(slug, []), key=lambda m: (-m.similarity, m.step_position))[
                    :max_steps
                ]
            ),
        )
        for slug in kept[:max_processes]
    )
