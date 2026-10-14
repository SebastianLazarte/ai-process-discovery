"""The product backlog: docs/requirements.toml is the source for the GitHub issues."""

import datetime
import tomllib
from pathlib import Path

DATA = tomllib.loads(
    (Path(__file__).resolve().parents[2] / "docs" / "requirements.toml").read_text(encoding="utf-8")
)
ROLES = set(DATA["product"]["roles"])
EPICS = DATA["user_requirements"]
ITEMS = DATA["requirement"]
REFINED = [r for r in ITEMS if "criteria" in r]
POINTS = {1, 2, 3, 5, 8}
PRIORITIES = {"must", "should", "could", "wont"}
AREAS = {"domain", "api", "llm", "reconciliation", "blueprint", "ui", "infra"}


def test_product_declares_goal_cadence_and_roles() -> None:
    product = DATA["product"]
    assert product["goal"].strip()
    assert product["sprint_days"] == 7
    assert isinstance(product["first_sprint"], datetime.date)
    assert ROLES


def test_requirement_ids_are_unique_and_contiguous() -> None:
    ids = [r["id"] for r in ITEMS]
    assert ids == [f"RS-{n:02d}" for n in range(1, len(ids) + 1)]


def test_epic_ids_are_contiguous() -> None:
    assert list(EPICS) == [f"RU-{n:02d}" for n in range(1, len(EPICS) + 1)]


def test_every_epic_is_a_user_story_for_a_declared_role() -> None:
    for ru, epic in EPICS.items():
        assert set(epic) == {"name", "as_a", "i_want", "so_that"}, ru
        assert epic["as_a"] in ROLES, ru
        assert all(epic[key].strip() for key in ("name", "i_want", "so_that")), ru


def test_every_epic_and_role_is_used() -> None:
    assert {r["ru"] for r in ITEMS} == set(EPICS)
    used_roles = {e["as_a"] for e in EPICS.values()} | {r["as_a"] for r in REFINED if "as_a" in r}
    assert used_roles == ROLES


def test_every_requirement_traces_to_an_epic_and_a_release() -> None:
    for r in ITEMS:
        assert r["ru"] in EPICS, r["id"]
        assert r["block"] in {f"B{n}" for n in range(13)}, r["id"]
        assert r["area"] in AREAS, r["id"]
        assert r["title"].strip(), r["id"]


def test_each_item_has_original_acceptance_or_refined_criteria() -> None:
    for r in ITEMS:
        assert ("acceptance" in r) != ("criteria" in r), r["id"]
        assert r.get("acceptance") or r.get("criteria"), r["id"]


def test_refined_items_meet_the_definition_of_ready() -> None:
    for r in REFINED:
        assert r["kind"] in {"story", "enabler"}, r["id"]
        if r["kind"] == "story":
            assert r["as_a"] in ROLES, r["id"]
            assert r["i_want"].strip() and r["so_that"].strip(), r["id"]
        else:
            assert not {"as_a", "i_want", "so_that"} & set(r), r["id"]
        assert r["points"] in POINTS, r["id"]
        assert r["priority"] in PRIORITIES, r["id"]
        for criterion in r["criteria"]:
            assert set(criterion) == {"given", "when", "then"}, r["id"]
            assert all(criterion[key].strip() for key in criterion), r["id"]


def test_refined_items_have_a_unique_rank() -> None:
    ranks = [r["rank"] for r in REFINED]
    assert all(isinstance(rank, int) and rank > 0 for rank in ranks)
    assert len(ranks) == len(set(ranks))
