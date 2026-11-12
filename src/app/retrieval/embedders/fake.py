"""Deterministic embedder for demos, CI and tests. No network, no key."""

import hashlib
import math
import re
from collections.abc import Sequence

from app.retrieval.embedder import InputType

DIMENSIONS = 256
_WORD = re.compile(r"[^\W_]+")
# Function words otherwise dominate short visitor descriptions (RS-119). Keep business
# terms, including verbs, unchanged. This is a small English lexical baseline, not a
# semantic or multilingual embedding model. A tokenisation change needs a new model id.
_ENGLISH_FUNCTION_WORDS = (
    "a an the and or but if then than as at by for from in into of on onto to with without "
    "about above after again against all am are be because been before being below between "
    "both can could did do does doing down during each few further had has have having he "
    "her here hers herself him himself his how i is it its itself me more most my myself "
    "no nor not off once only other our ours ourselves out over own same she should so some "
    "such that their theirs them themselves there these they this those through too under "
    "until up us very was we were what when where which while who whom why will would you "
    "your yours yourself yourselves"
)
_STOP_WORDS = frozenset(_ENGLISH_FUNCTION_WORDS.split())


class FakeEmbedder:
    """Hashes lowercased content words into a normalised vector.

    Texts that share words get a higher dot product than texts that share none, which is
    close enough to keyword overlap for tests to assert what retrieval returns. The hash is
    ``hashlib``, never the built-in ``hash()``, so vectors are the same in every process.
    """

    @property
    def name(self) -> str:
        return "fake"

    @property
    def model(self) -> str:
        return f"fake-hash-{DIMENSIONS}-v2"

    def embed(self, texts: Sequence[str], input_type: InputType) -> list[tuple[float, ...]]:
        # ``input_type`` is accepted for the protocol; the fake treats both the same way.
        return [_embed_text(text) for text in texts]


def _embed_text(text: str) -> tuple[float, ...]:
    counts = [0.0] * DIMENSIONS
    for word in _WORD.findall(text.lower()):
        if word in _STOP_WORDS:
            continue
        digest = hashlib.sha256(word.encode("utf-8")).digest()
        counts[int.from_bytes(digest[:8], "big") % DIMENSIONS] += 1.0
    norm = math.sqrt(sum(value * value for value in counts))
    if norm == 0.0:
        return tuple(counts)
    return tuple(value / norm for value in counts)
