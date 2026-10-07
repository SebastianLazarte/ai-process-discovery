"""Traceability: docs/requirements.toml is the source for the GitHub issues."""

import tomllib
from pathlib import Path

DATA = tomllib.loads(
    (Path(__file__).resolve().parents[2] / "docs" / "requirements.toml").read_text(encoding="utf-8")
)


def test_requirement_ids_are_unique_and_contiguous() -> None:
    ids = [r["id"] for r in DATA["requirement"]]
    assert ids == [f"RS-{n:02d}" for n in range(1, len(ids) + 1)]


def test_every_requirement_traces_to_a_user_requirement() -> None:
    user_ids = set(DATA["user_requirements"])
    for requirement in DATA["requirement"]:
        assert requirement["ru"] in user_ids, requirement["id"]
        assert requirement["acceptance"], requirement["id"]
        assert requirement["block"] in {f"B{n}" for n in range(10)}, requirement["id"]
