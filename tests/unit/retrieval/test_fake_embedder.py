"""FakeEmbedder: deterministic, normalised, offline, keyword-like similarity (RS-117)."""

import math
import os
import subprocess
import sys

import pytest

from app.retrieval.embedder import Embedder
from app.retrieval.embedders.fake import FakeEmbedder


def _dot(a: tuple[float, ...], b: tuple[float, ...]) -> float:
    return sum(x * y for x, y in zip(a, b, strict=True))


def _embed_one(text: str) -> tuple[float, ...]:
    return FakeEmbedder().embed([text], "document")[0]


def _signature(vector: tuple[float, ...]) -> float:
    return sum((i + 1) * x for i, x in enumerate(vector))


@pytest.mark.req("RS-117", criterion=1)
def test_the_same_text_gives_the_same_vector_twice() -> None:
    embedder = FakeEmbedder()
    first = embedder.embed(["Check the policy"], "query")
    assert embedder.embed(["Check the policy"], "query") == first


@pytest.mark.req("RS-117", criterion=1)
def test_the_vector_does_not_depend_on_the_hash_seed_of_the_process() -> None:
    code = (
        "from app.retrieval.embedders.fake import FakeEmbedder;"
        "v = FakeEmbedder().embed(['Check the policy'], 'document')[0];"
        "print(repr(sum((i + 1) * x for i, x in enumerate(v))))"
    )
    env = {**os.environ, "PYTHONHASHSEED": "12345"}
    out = subprocess.run(
        [sys.executable, "-c", code], capture_output=True, text=True, check=True, env=env
    ).stdout
    assert float(out) == pytest.approx(_signature(_embed_one("Check the policy")))


@pytest.mark.req("RS-117", criterion=1)
def test_the_vector_has_256_dimensions() -> None:
    assert len(_embed_one("Check the policy and the cover")) == 256


@pytest.mark.req("RS-117", criterion=1)
def test_the_vector_has_unit_length() -> None:
    vector = _embed_one("Check the policy and the cover")
    assert math.sqrt(_dot(vector, vector)) == pytest.approx(1.0)


@pytest.mark.req("RS-117", criterion=1)
def test_a_text_without_words_gives_the_zero_vector() -> None:
    assert _embed_one("  ... !!! ") == (0.0,) * 256


@pytest.mark.req("RS-117", criterion=1)
def test_one_vector_comes_back_per_text_in_order() -> None:
    texts = ["claims intake", "invoice approval", "claims intake"]
    vectors = FakeEmbedder().embed(texts, "document")
    assert vectors == [_embed_one(text) for text in texts]


@pytest.mark.req("RS-117", criterion=1)
def test_no_texts_give_no_vectors() -> None:
    assert FakeEmbedder().embed([], "query") == []


@pytest.mark.req("RS-117", criterion=1)
def test_the_input_type_does_not_change_the_vector() -> None:
    embedder = FakeEmbedder()
    as_query = embedder.embed(["Check the policy"], "query")
    assert embedder.embed(["Check the policy"], "document") == as_query


@pytest.mark.req("RS-117", criterion=1)
def test_case_and_punctuation_do_not_change_the_vector() -> None:
    assert _embed_one("Check the Policy!") == _embed_one("check the policy")


@pytest.mark.req("RS-117", criterion=2)
def test_texts_that_share_words_are_more_similar_than_texts_that_share_none() -> None:
    query = _embed_one("approve the supplier invoice")
    related = _embed_one("Invoice approval for a supplier")
    unrelated = _embed_one("Pick and pack the warehouse order")
    assert _dot(query, related) > _dot(query, unrelated)


@pytest.mark.req("RS-117", criterion=2)
def test_texts_that_share_no_words_have_no_similarity() -> None:
    assert _dot(_embed_one("alpha beta"), _embed_one("gamma delta")) == pytest.approx(0.0)


def test_the_fake_embedder_names_itself() -> None:
    embedder = FakeEmbedder()
    assert (embedder.name, embedder.model) == ("fake", "fake-hash-256")


def test_the_fake_embedder_satisfies_the_protocol() -> None:
    embedder: Embedder = FakeEmbedder()
    assert embedder.name == "fake"
