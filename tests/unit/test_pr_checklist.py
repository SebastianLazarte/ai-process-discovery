"""The pull request checklist: areas by changed file, questions by type, ticks preserved."""

import re
from pathlib import Path

import pytest
from scripts.pr_checklist import (
    MARKER,
    checked_items,
    load_config,
    matching_areas,
    pr_type,
    render,
)

ROOT = Path(__file__).resolve().parents[2]
CONFIG = load_config()
REPO = "owner/name"


def titles(files: list[str]) -> list[str]:
    return [area.title for area in matching_areas(CONFIG, files)]


def test_a_web_change_lists_only_the_web_client() -> None:
    assert titles(["web/app.js"]) == ["Web client"]


def test_a_change_in_several_areas_lists_each_once_in_config_order() -> None:
    assert titles(["web/app.js", "src/app/llm/prompts.py", "web/views.js"]) == [
        "LLM layer",
        "Web client",
    ]


def test_files_outside_every_area_get_only_the_common_items() -> None:
    assert titles(["LICENSE"]) == []
    body = render(CONFIG, ["LICENSE"], "chore: x", REPO, set())
    assert "#### Every pull request" in body
    assert "none of the listed areas" in body


@pytest.mark.parametrize(
    ("title", "expected"),
    [
        ("feat(web): add x", "feat"),
        ("fix!: drop y", "fix"),
        ("ci: pin actions", "ci"),
        ("Update readme", None),
    ],
)
def test_pr_type(title: str, expected: str | None) -> None:
    assert pr_type(title) == expected


def test_questions_follow_the_type_and_fall_back_to_the_default() -> None:
    fix = render(CONFIG, [], "fix: x", REPO, set())
    assert CONFIG.verification["fix"][0] in fix
    other = render(CONFIG, [], "Update readme", REPO, set())
    assert CONFIG.verification["default"][0] in other


def test_the_comment_starts_with_the_marker() -> None:
    assert render(CONFIG, [], "ci: x", REPO, set()).startswith(MARKER)


def test_ticked_items_survive_a_new_render() -> None:
    first = render(CONFIG, ["web/app.js"], "feat(web): x", REPO, set())
    item = CONFIG.areas[[a.title for a in CONFIG.areas].index("Web client")].items[0].text
    ticked = first.replace(f"- [ ] {item}<br>", f"- [x] {item}<br>")
    assert checked_items(ticked) == {item}

    again = render(CONFIG, ["web/app.js", "src/app/llm/prompts.py"], "feat: x", REPO, {item})
    assert f"- [x] {item}<br>" in again
    assert again.count("- [x] ") == 1


def test_a_ticked_item_that_no_longer_applies_is_dropped() -> None:
    item = CONFIG.areas[0].items[0].text
    body = render(CONFIG, ["web/app.js"], "feat: x", REPO, {item})
    assert "- [x] " not in body


# Drift guards: the config must keep describing the repository as it is.


def test_every_local_ref_exists() -> None:
    for area in (CONFIG.always, *CONFIG.areas):
        for item in area.items:
            if not item.ref.startswith("https://"):
                assert (ROOT / item.ref).exists(), item.ref


def test_every_area_path_exists() -> None:
    for area in CONFIG.areas:
        for path in area.paths:
            assert (ROOT / path).exists(), f"{area.title}: {path}"


def test_every_title_type_has_questions() -> None:
    workflow = (ROOT / ".github" / "workflows" / "pr-title.yml").read_text(encoding="utf-8")
    types_block = re.search(r"types: \|\n((?:\s+\w+\n)+)", workflow)
    assert types_block is not None
    types = types_block.group(1).split()
    assert types
    assert set(types) <= set(CONFIG.verification)
