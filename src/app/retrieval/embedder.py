from collections.abc import Sequence
from typing import Literal, Protocol

InputType = Literal["query", "document"]


class Embedder(Protocol):
    """What retrieval needs from any embedding model (ADR 0021).

    Kept apart from ``LLMProvider``: embedding and generation change for different reasons
    and come from different vendors.
    """

    @property
    def name(self) -> str:
        """The provider, as ``embedding_provider`` names it."""

    @property
    def model(self) -> str:
        """The embedding model; an index built with one model is only read with the same."""

    def embed(self, texts: Sequence[str], input_type: InputType) -> list[tuple[float, ...]]:
        """One vector per text, in the order of ``texts``.

        ``query`` is a short search text and ``document`` a catalog chunk; models trained
        for retrieval embed the two differently.
        """
