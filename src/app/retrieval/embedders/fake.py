"""Deterministic embedder for demos, CI and tests. No network, no key."""

import hashlib
import math
import re
from collections.abc import Sequence

from app.retrieval.embedder import InputType

DIMENSIONS = 256
_WORD = re.compile(r"[^\W_]+")


class FakeEmbedder:
    """Hashes the lowercased words of a text into a normalised vector.

    Texts that share words get a higher dot product than texts that share none, which is
    close enough to keyword overlap for tests to assert what retrieval returns. The hash is
    ``hashlib``, never the built-in ``hash()``, so vectors are the same in every process.
    """

    @property
    def name(self) -> str:
        return "fake"

    @property
    def model(self) -> str:
        return f"fake-hash-{DIMENSIONS}"

    def embed(self, texts: Sequence[str], input_type: InputType) -> list[tuple[float, ...]]:
        # ``input_type`` is accepted for the protocol; the fake treats both the same way.
        return [_embed_text(text) for text in texts]


def _embed_text(text: str) -> tuple[float, ...]:
    counts = [0.0] * DIMENSIONS
    for word in _WORD.findall(text.lower()):
        digest = hashlib.sha256(word.encode("utf-8")).digest()
        counts[int.from_bytes(digest[:8], "big") % DIMENSIONS] += 1.0
    norm = math.sqrt(sum(value * value for value in counts))
    if norm == 0.0:
        return tuple(counts)
    return tuple(value / norm for value in counts)
