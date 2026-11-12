from collections.abc import Sequence
from typing import Literal, Protocol

InputType = Literal["query", "document"]


class Embedder(Protocol):
    """What retrieval needs from any embedding model (ADR 0021).

    Kept apart from ``LLMProvider``: embedding and generation change for different reasons
    and come from different vendors.
    """

    @property
    def name(self) -> str: ...

    @property
    def model(self) -> str: ...

    def embed(self, texts: Sequence[str], input_type: InputType) -> list[tuple[float, ...]]:
        """One vector per text, in the order of ``texts``.

        ``query`` is a short search text and ``document`` a catalog chunk; models trained
        for retrieval embed the two differently.
        """
        ...
