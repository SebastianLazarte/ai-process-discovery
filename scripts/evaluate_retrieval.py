"""Offline retrieval regression report and threshold sweep (RS-119).

Run ``uv run python scripts/evaluate_retrieval.py --check``. This command always uses the
fake embedder, ignores .env and never calls a paid provider. ``evaluate`` also accepts a
real service's retrieve method for the separately authorised provider evaluation (RS-120).
The gold set is calibration data, not a held-out estimate of visitor success.
"""

import argparse
import hashlib
import json
import sys
from collections.abc import Callable, Sequence
from dataclasses import asdict, dataclass
from pathlib import Path

from app.core.config import DEFAULT_RETRIEVAL_THRESHOLDS
from app.domain.retrieval import RetrievedProcess
from app.retrieval.embedders.fake import FakeEmbedder
from app.retrieval.index import build_index
from app.services.retrieval_service import RetrievalService
from app.services.template_service import catalog_files

GOLD_PATH = Path(__file__).resolve().parents[1] / "tests" / "fixtures" / "retrieval_gold.json"
# Fixed regression gates, changed only with a documented evaluation, never at test runtime.
MIN_RECALL_AT_3 = 0.60
MIN_MRR = 0.60


@dataclass(frozen=True)
class GoldCase:
    id: str
    description: str
    expected_slug: str | None


@dataclass(frozen=True)
class CaseResult:
    id: str
    expected_slug: str | None
    retrieved: tuple[str, ...]
    reciprocal_rank: float


@dataclass(frozen=True)
class Evaluation:
    positive_cases: int
    negative_cases: int
    recall_at_3: float
    mrr: float
    no_match_accuracy: float
    cases: tuple[CaseResult, ...]


def load_gold_set(path: Path = GOLD_PATH) -> tuple[GoldCase, ...]:
    data = json.loads(path.read_text(encoding="utf-8"))
    positives = [
        GoldCase(f"{slug}-{position}", text, slug)
        for slug, descriptions in data["processes"].items()
        for position, text in enumerate(descriptions, 1)
    ]
    negatives = [
        GoldCase(f"unmatched-{position}", text, None)
        for position, text in enumerate(data["unmatched"], 1)
    ]
    return tuple(positives + negatives)


def evaluate(
    cases: Sequence[GoldCase],
    retrieve: Callable[[str], Sequence[RetrievedProcess]],
) -> Evaluation:
    """Recall@3 and MRR@3 over positives; rejection accuracy over negatives separately.

    Every positive has one relevant process. A miss contributes zero even when retrieval
    abstains. A result after rank three is a miss, as the product returns at most three.
    """
    rows = []
    for case in cases:
        slugs = tuple(match.process_slug for match in retrieve(case.description)[:3])
        rr = 1.0 / (slugs.index(case.expected_slug) + 1) if case.expected_slug in slugs else 0.0
        rows.append(CaseResult(case.id, case.expected_slug, slugs, rr))
    positives = [row for row in rows if row.expected_slug is not None]
    negatives = [row for row in rows if row.expected_slug is None]
    if not positives or not negatives:
        raise ValueError("the gold set must contain positive and negative cases")
    return Evaluation(
        positive_cases=len(positives),
        negative_cases=len(negatives),
        recall_at_3=sum(row.reciprocal_rank > 0 for row in positives) / len(positives),
        mrr=sum(row.reciprocal_rank for row in positives) / len(positives),
        no_match_accuracy=sum(not row.retrieved for row in negatives) / len(negatives),
        cases=tuple(rows),
    )


def _passes(result: Evaluation) -> bool:
    return (
        result.recall_at_3 >= MIN_RECALL_AT_3
        and result.mrr >= MIN_MRR
        and result.no_match_accuracy == 1.0
    )


def _threshold(value: str) -> float:
    number = float(value)
    if not -1.0 <= number <= 1.0:
        raise argparse.ArgumentTypeError("threshold must be finite and between -1 and 1")
    return number


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--threshold", type=_threshold, help="override the calibrated fake threshold")
    mode.add_argument(
        "--sweep", nargs="+", type=_threshold, help="compare thresholds on the same set"
    )
    parser.add_argument("--check", action="store_true", help="exit 1 if a regression gate fails")
    args = parser.parse_args(argv)
    embedder = FakeEmbedder()
    index = build_index(embedder, catalog_files())
    # Do not let an operator's environment change the offline regression baseline.
    threshold = (
        args.threshold
        if args.threshold is not None
        else DEFAULT_RETRIEVAL_THRESHOLDS[embedder.model]
    )
    cases = load_gold_set()
    result = evaluate(cases, RetrievalService(embedder, index, threshold).retrieve)
    gold = GOLD_PATH.read_text(encoding="utf-8")
    report = {
        "model": embedder.model,
        "catalog_hash": index.catalog_hash,
        "gold_version": json.loads(gold)["version"],
        "gold_sha256": hashlib.sha256(gold.encode("utf-8")).hexdigest(),
        "threshold": threshold,
        "floors": {"recall_at_3": MIN_RECALL_AT_3, "mrr": MIN_MRR, "no_match_accuracy": 1.0},
        "metrics": asdict(result),
    }
    if args.sweep:
        report["sweep"] = [
            {
                "threshold": candidate,
                **asdict(evaluate(cases, RetrievalService(embedder, index, candidate).retrieve)),
            }
            for candidate in args.sweep
        ]
    sys.stdout.write(json.dumps(report, indent=2) + "\n")
    return int(args.check and not _passes(result))


if __name__ == "__main__":
    raise SystemExit(main())
