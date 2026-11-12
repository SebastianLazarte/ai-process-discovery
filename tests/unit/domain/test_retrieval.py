"""Ranking of catalog processes against a description (RS-116, ADR 0021).

Chunk vectors here are ``(similarity, 0.0)`` and the query is ``(1.0, 0.0)``, so the
dot product is the similarity itself and every expected value is exact.
"""

import ast
import sys
from pathlib import Path

import pytest

from app.domain.errors import DomainValidationError
from app.domain.retrieval import CatalogChunk, RetrievedProcess, StepMatch, rank_processes

QUERY = (1.0, 0.0)
THRESHOLD = 0.5
DOMAIN_RETRIEVAL = Path(__file__).resolve().parents[3] / "src" / "app" / "domain" / "retrieval.py"


def chunk(slug: str, position: int | None, similarity: float) -> CatalogChunk:
    return CatalogChunk(process_slug=slug, step_position=position, vector=(similarity, 0.0))


def rank(chunks: list[CatalogChunk], **limits: int) -> tuple[RetrievedProcess, ...]:
    return rank_processes(QUERY, chunks, threshold=THRESHOLD, **limits)


def slugs(result: tuple[RetrievedProcess, ...]) -> list[str]:
    return [process.process_slug for process in result]


@pytest.mark.req("RS-116", criterion=1)
def test_a_process_scores_as_its_best_step_chunk() -> None:
    (found,) = rank([chunk("a", None, 0.6), chunk("a", 1, 0.75), chunk("a", 2, 0.5)])

    assert found.similarity == 0.75


@pytest.mark.req("RS-116", criterion=1)
def test_a_process_scores_as_its_process_level_chunk_when_that_is_best() -> None:
    (found,) = rank([chunk("a", 1, 0.5), chunk("a", None, 0.875), chunk("a", 2, 0.625)])

    assert found.similarity == 0.875


@pytest.mark.req("RS-116", criterion=1)
def test_processes_come_best_first_with_their_best_steps_first() -> None:
    result = rank(
        [
            chunk("low", None, 0.625),
            chunk("high", 1, 0.75),
            chunk("high", 2, 0.875),
            chunk("high", None, 0.5),
            chunk("mid", 3, 0.6875),
        ]
    )

    assert result == (
        RetrievedProcess("high", 0.875, (StepMatch(2, 0.875), StepMatch(1, 0.75))),
        RetrievedProcess("mid", 0.6875, (StepMatch(3, 0.6875),)),
        RetrievedProcess("low", 0.625, ()),
    )


@pytest.mark.req("RS-116", criterion=1)
def test_only_the_top_three_processes_are_kept_by_default() -> None:
    chunks = [chunk(slug, None, sim) for slug, sim in (("a", 0.5), ("b", 0.75), ("c", 0.625))]
    chunks.append(chunk("d", None, 0.875))

    assert slugs(rank(chunks)) == ["d", "b", "c"]


@pytest.mark.req("RS-116", criterion=1)
def test_the_number_of_processes_follows_max_processes() -> None:
    chunks = [chunk("a", None, 0.75), chunk("b", None, 0.875)]

    assert slugs(rank(chunks, max_processes=1)) == ["b"]
    assert slugs(rank(chunks, max_processes=2)) == ["b", "a"]


@pytest.mark.req("RS-116", criterion=1)
def test_only_the_top_three_steps_of_a_process_are_kept_by_default() -> None:
    chunks = [chunk("a", position, 0.5 + position / 16) for position in (1, 2, 3, 4)]

    (found,) = rank(chunks)

    assert [match.step_position for match in found.steps] == [4, 3, 2]


@pytest.mark.req("RS-116", criterion=1)
def test_the_number_of_steps_follows_max_steps() -> None:
    chunks = [chunk("a", 1, 0.625), chunk("a", 2, 0.75)]

    (one,) = rank(chunks, max_steps=1)
    (two,) = rank(chunks, max_steps=2)

    assert one.steps == (StepMatch(2, 0.75),)
    assert two.steps == (StepMatch(2, 0.75), StepMatch(1, 0.625))


@pytest.mark.req("RS-116", criterion=1)
def test_steps_below_the_threshold_are_left_out_of_a_retrieved_process() -> None:
    (found,) = rank([chunk("a", 1, 0.875), chunk("a", 2, 0.4375)])

    assert found.steps == (StepMatch(1, 0.875),)


@pytest.mark.req("RS-116", criterion=1)
def test_a_process_matched_only_by_its_process_level_chunk_has_no_steps() -> None:
    (found,) = rank([chunk("a", None, 0.75), chunk("a", 1, 0.25)])

    assert found == RetrievedProcess("a", 0.75, ())


@pytest.mark.req("RS-116", criterion=1)
def test_a_process_level_chunk_is_never_listed_as_a_step() -> None:
    (found,) = rank([chunk("a", None, 0.875), chunk("a", 1, 0.75)])

    assert found.steps == (StepMatch(1, 0.75),)


@pytest.mark.req("RS-116", criterion=1)
def test_the_similarity_is_the_dot_product_of_query_and_chunk() -> None:
    result = rank_processes(
        (0.5, 0.25, 1.0),
        [CatalogChunk("a", None, (0.5, 1.0, 0.25))],
        threshold=0.0,
    )

    assert result == (RetrievedProcess("a", 0.75, ()),)


@pytest.mark.req("RS-116", criterion=1)
def test_chunks_of_different_processes_do_not_share_steps() -> None:
    result = rank([chunk("a", 1, 0.75), chunk("b", 2, 0.625)])

    assert result == (
        RetrievedProcess("a", 0.75, (StepMatch(1, 0.75),)),
        RetrievedProcess("b", 0.625, (StepMatch(2, 0.625),)),
    )


@pytest.mark.req("RS-116", criterion=2)
def test_no_chunks_retrieve_nothing() -> None:
    assert rank([]) == ()


@pytest.mark.req("RS-116", criterion=2)
def test_a_score_just_below_the_threshold_is_not_retrieved() -> None:
    assert rank([chunk("a", None, 0.4999), chunk("a", 1, 0.49)]) == ()


@pytest.mark.req("RS-116", criterion=2)
def test_a_score_exactly_at_the_threshold_is_retrieved() -> None:
    assert rank([chunk("a", None, 0.5)]) == (RetrievedProcess("a", 0.5, ()),)


@pytest.mark.req("RS-116", criterion=2)
def test_a_step_exactly_at_the_threshold_is_kept_and_one_just_below_is_not() -> None:
    (found,) = rank([chunk("a", 1, 0.5), chunk("a", 2, 0.4999)])

    assert found.steps == (StepMatch(1, 0.5),)


@pytest.mark.req("RS-116", criterion=2)
def test_a_negative_similarity_is_not_retrieved() -> None:
    assert rank_processes(QUERY, [chunk("a", 1, -0.75)], threshold=0.0) == ()


@pytest.mark.req("RS-116", criterion=3)
def test_processes_with_the_same_score_come_in_slug_order() -> None:
    chunks = [chunk("b", None, 0.75), chunk("c", None, 0.75), chunk("a", None, 0.75)]

    assert slugs(rank(chunks)) == ["a", "b", "c"]


@pytest.mark.req("RS-116", criterion=3)
def test_a_tie_does_not_beat_a_better_score() -> None:
    chunks = [chunk("a", None, 0.625), chunk("b", None, 0.75), chunk("c", None, 0.75)]

    assert slugs(rank(chunks)) == ["b", "c", "a"]


@pytest.mark.req("RS-116", criterion=3)
def test_steps_with_the_same_similarity_come_in_position_order() -> None:
    chunks = [chunk("a", 3, 0.75), chunk("a", 1, 0.75), chunk("a", 2, 0.75)]

    (found,) = rank(chunks)

    assert [match.step_position for match in found.steps] == [1, 2, 3]


@pytest.mark.req("RS-116", criterion=3)
def test_the_cut_at_max_processes_keeps_the_smaller_slug_in_a_tie() -> None:
    chunks = [chunk("b", None, 0.75), chunk("a", None, 0.75)]

    assert slugs(rank(chunks, max_processes=1)) == ["a"]


@pytest.mark.req("RS-116", criterion=3)
def test_the_cut_at_max_steps_keeps_the_smaller_position_in_a_tie() -> None:
    chunks = [chunk("a", 2, 0.75), chunk("a", 1, 0.75)]

    (found,) = rank(chunks, max_steps=1)

    assert found.steps == (StepMatch(1, 0.75),)


@pytest.mark.req("RS-116", criterion=3)
def test_the_order_of_the_chunks_does_not_change_the_result() -> None:
    chunks = [
        chunk("b", None, 0.75),
        chunk("a", 2, 0.75),
        chunk("a", 1, 0.75),
        chunk("b", 1, 0.625),
        chunk("c", 4, 0.5),
    ]

    assert rank(chunks) == rank(list(reversed(chunks)))


def test_a_vector_of_another_length_than_the_query_is_rejected_naming_the_field() -> None:
    bad = CatalogChunk("a", 1, (0.5, 0.5, 0.5))

    with pytest.raises(DomainValidationError) as raised:
        rank_processes(QUERY, [chunk("b", None, 0.75), bad], threshold=THRESHOLD)

    assert raised.value.field == "vector"


def test_a_vector_of_another_length_is_rejected_even_when_it_would_not_match() -> None:
    with pytest.raises(DomainValidationError):
        rank_processes(QUERY, [CatalogChunk("a", 1, (0.0,))], threshold=THRESHOLD)


@pytest.mark.parametrize("limit", ["max_processes", "max_steps"])
def test_a_negative_limit_is_rejected_naming_the_field(limit: str) -> None:
    with pytest.raises(DomainValidationError) as raised:
        rank([chunk("a", 1, 0.75)], **{limit: -1})

    assert raised.value.field == limit


def test_a_limit_of_zero_keeps_nothing() -> None:
    chunks = [chunk("a", 1, 0.75)]

    assert rank(chunks, max_processes=0) == ()
    assert rank(chunks, max_steps=0) == (RetrievedProcess("a", 0.75, ()),)


@pytest.mark.req("RS-116", criterion=4)
def test_the_ranking_module_imports_only_the_standard_library_and_the_domain() -> None:
    imported: set[str] = set()
    for node in ast.walk(ast.parse(DOMAIN_RETRIEVAL.read_text(encoding="utf-8"))):
        if isinstance(node, ast.Import):
            imported.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            imported.add(node.module)

    outside = {
        module
        for module in imported
        if module.split(".")[0] not in sys.stdlib_module_names
        and not (module == "app.domain" or module.startswith("app.domain."))
    }
    assert outside == set()
