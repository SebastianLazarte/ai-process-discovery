"""Turn mutmut's CI stats into a score and fail below a minimum (ADR 0011).

The score is killed mutants over mutants that ran: a mutant no test reaches counts
against it, so uncovered code cannot hide. Run by .github/workflows/mutation.yml:

    uv run mutmut export-cicd-stats
    uv run python scripts/mutation_score.py mutants/mutmut-cicd-stats.json --min 83
"""

import argparse
import json
import sys
from decimal import Decimal
from pathlib import Path


def score(stats: dict[str, int]) -> Decimal:
    ran = stats["total"] - stats["skipped"]
    if ran == 0:
        return Decimal(0)
    return (Decimal(100) * stats["killed"] / ran).quantize(Decimal("0.1"))


def report(stats: dict[str, int], minimum: Decimal) -> tuple[str, bool]:
    value = score(stats)
    passed = value >= minimum
    lines = [
        "## Mutation score (domain)",
        "",
        f"**{value}%** killed, minimum {minimum}%: {'pass' if passed else 'FAIL'}",
        "",
        "| Killed | Survived | No tests | Timeout | Total |",
        "|---|---|---|---|---|",
        f"| {stats['killed']} | {stats['survived']} | {stats['no_tests']} "
        f"| {stats['timeout']} | {stats['total']} |",
    ]
    return "\n".join(lines), passed


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stats", type=Path)
    parser.add_argument("--min", type=Decimal, required=True, dest="minimum")
    args = parser.parse_args(argv)
    text, passed = report(json.loads(args.stats.read_text(encoding="utf-8")), args.minimum)
    sys.stdout.write(text + "\n")
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
