"""RS-119: score real visitor-style fixtures and keep misses in the denominator."""

import json
from collections import Counter
from pathlib import Path

import pytest
from pydantic import ValidationError
from scripts import evaluate_retrieval as evaluation

from app.core.config import Settings
from app.domain.retrieval import RetrievedProcess
from app.llm.provider import LLMConfigurationError
from app.retrieval.embedders.fake import FakeEmbedder
from app.services.retrieval_service import build_retrieval_service
from app.services.template_service import catalog_files


@pytest.mark.req("RS-119", criterion=1)
def test_gold_covers_every_current_process_twice_and_contains_unmatched_descriptions() -> None:
    cases = evaluation.load_gold_set()
    templates = [t for sector in catalog_files().values() for t in sector["templates"]]
    counts = Counter(case.expected_slug for case in cases if case.expected_slug is not None)
    assert set(counts) == {t["slug"] for t in templates}
    assert min(counts.values()) >= 2
    assert sum(case.expected_slug is None for case in cases) >= 5
    texts = [case.description.strip().casefold() for case in cases]
    assert len(set(texts)) == len(texts)
    assert all(texts)
    assert len({case.id for case in cases}) == len(cases)
    catalog_descriptions = {t["description"].casefold() for t in templates}
    assert not catalog_descriptions.intersection(texts)


@pytest.mark.req("RS-119", criterion=2)
def test_metrics_count_misses_and_do_not_mix_negative_cases_into_recall() -> None:
    cases = tuple(
        evaluation.GoldCase(str(i), str(i), slug)
        for i, slug in enumerate(["a", "b", "c", "d", None, None])
    )
    rankings = [("a",), ("x", "b"), ("x", "y", "c"), ("x", "y", "z", "d"), (), ("a",)]

    def retrieve(text: str) -> tuple[RetrievedProcess, ...]:
        return tuple(RetrievedProcess(slug, 0.8, ()) for slug in rankings[int(text)])

    result = evaluation.evaluate(cases, retrieve)
    assert result.recall_at_3 == 0.75
    assert result.mrr == pytest.approx((1 + 1 / 2 + 1 / 3) / 4)
    assert result.no_match_accuracy == 0.5
    assert result.positive_cases == 4
    assert result.negative_cases == 2
    assert [row.reciprocal_rank for row in result.cases] == [1, 0.5, 1 / 3, 0, 0, 0]


@pytest.mark.parametrize("expected", ["a", None])
def test_an_evaluation_requires_both_positive_and_negative_cases(expected: str | None) -> None:
    with pytest.raises(ValueError, match="positive and negative"):
        evaluation.evaluate((evaluation.GoldCase("one", "text", expected),), lambda _: ())


@pytest.mark.req("RS-119", criterion=2)
def test_fake_retrieval_meets_fixed_regression_floors() -> None:
    service = build_retrieval_service(Settings(_env_file=None, embedding_provider="fake"))
    result = evaluation.evaluate(evaluation.load_gold_set(), service.retrieve)
    assert result.recall_at_3 >= evaluation.MIN_RECALL_AT_3, result
    assert result.mrr >= evaluation.MIN_MRR, result


@pytest.mark.req("RS-119", criterion=3)
def test_every_unmatched_description_returns_nothing() -> None:
    service = build_retrieval_service(Settings(_env_file=None, embedding_provider="fake"))
    failures = {
        case.id: [match.process_slug for match in service.retrieve(case.description)]
        for case in evaluation.load_gold_set()
        if case.expected_slug is None and service.retrieve(case.description)
    }
    assert failures == {}


@pytest.mark.req("RS-119", criterion=4)
def test_threshold_is_selected_by_the_actual_embedding_model() -> None:
    model = FakeEmbedder().model
    settings = Settings(_env_file=None, retrieval_thresholds={model: 0.42, "another-model": 0.91})
    assert build_retrieval_service(settings).threshold == 0.42


@pytest.mark.req("RS-119", criterion=4)
def test_an_uncalibrated_model_fails_instead_of_using_another_models_threshold() -> None:
    with pytest.raises(LLMConfigurationError, match="threshold"):
        build_retrieval_service(Settings(_env_file=None, retrieval_thresholds={}))


@pytest.mark.req("RS-119", criterion=4)
def test_explicit_legacy_threshold_remains_an_override_even_when_zero() -> None:
    settings = Settings(_env_file=None, retrieval_thresholds={}, retrieval_threshold=0.0)
    assert build_retrieval_service(settings).threshold == 0.0


@pytest.mark.req("RS-119", criterion=4)
@pytest.mark.parametrize("value", [-1.01, 1.01, float("nan"), float("inf")])
def test_invalid_thresholds_are_rejected(value: float) -> None:
    with pytest.raises(ValidationError):
        Settings(_env_file=None, retrieval_thresholds={"test-model": value})
    with pytest.raises(ValidationError):
        Settings(_env_file=None, retrieval_threshold=value)


@pytest.mark.req("RS-119", criterion=4)
def test_model_thresholds_can_be_configured_as_environment_json(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    model = FakeEmbedder().model
    monkeypatch.setenv("RETRIEVAL_THRESHOLDS", json.dumps({model: 0.48}))
    monkeypatch.delenv("RETRIEVAL_THRESHOLD", raising=False)
    assert build_retrieval_service(Settings(_env_file=None)).threshold == 0.48


def test_cli_emits_reproducible_json_without_the_descriptions(
    capsys: pytest.CaptureFixture[str],
) -> None:
    assert evaluation.main(["--check"]) == 0
    output = json.loads(capsys.readouterr().out)
    assert output["model"] == FakeEmbedder().model
    assert output["catalog_hash"]
    assert output["gold_version"] == 1
    assert output["gold_sha256"]
    assert output["metrics"]["no_match_accuracy"] == 1.0
    assert "description" not in json.dumps(output)


def test_cli_returns_failure_when_a_threshold_destroys_recall(
    capsys: pytest.CaptureFixture[str],
) -> None:
    assert evaluation.main(["--threshold", "1", "--check"]) == 1
    assert json.loads(capsys.readouterr().out)["metrics"]["recall_at_3"] == 0


def test_sweep_reports_each_threshold_and_its_false_positives(
    capsys: pytest.CaptureFixture[str],
) -> None:
    assert evaluation.main(["--sweep", "0", "1"]) == 0
    output = json.loads(capsys.readouterr().out)
    assert [row["threshold"] for row in output["sweep"]] == [0.0, 1.0]
    assert output["sweep"][0]["no_match_accuracy"] == 0
    assert output["sweep"][1]["recall_at_3"] == 0


def test_example_environment_keeps_the_calibrated_model_defaults() -> None:
    root = Path(__file__).resolve().parents[2]
    settings = Settings(_env_file=root / ".env.example")
    service = build_retrieval_service(settings)
    default = build_retrieval_service(Settings(_env_file=None))
    assert service.threshold == default.threshold
