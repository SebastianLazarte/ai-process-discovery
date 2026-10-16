"""The weekly mutation job fails when the domain tests stop catching injected bugs."""

import json
from decimal import Decimal
from pathlib import Path

from scripts.mutation_score import main, report, score

STATS = {"killed": 672, "survived": 129, "no_tests": 4, "timeout": 0, "skipped": 0, "total": 805}


def test_score_is_killed_over_mutants_that_ran() -> None:
    assert score(STATS) == Decimal("83.5")


def test_mutants_without_tests_count_against_the_score() -> None:
    assert score({**STATS, "killed": 668, "no_tests": 8}) < score(STATS)


def test_no_mutants_scores_zero() -> None:
    assert score({**STATS, "killed": 0, "total": 0}) == 0


def test_report_passes_at_the_minimum_and_fails_below_it() -> None:
    assert report(STATS, Decimal("83.5"))[1] is True
    assert report(STATS, Decimal("83.6"))[1] is False


def test_main_exit_code_follows_the_minimum(tmp_path: Path) -> None:
    path = tmp_path / "stats.json"
    path.write_text(json.dumps(STATS), encoding="utf-8")
    assert main([str(path), "--min", "80"]) == 0
    assert main([str(path), "--min", "90"]) == 1
