"""Issue bodies are built from the backlog, and a sync keeps ticked criteria."""

from typing import Any

from scripts.bootstrap_github import (
    criteria_lines,
    issue_body,
    issue_edits,
    issue_labels,
    ticked_criteria,
    user_story,
)

EPICS = {
    "RU-01": {
        "name": "Process modelling",
        "as_a": "operations lead",
        "i_want": "to map a process",
        "so_that": "I can analyse it",
    },
}
DELIVERED: dict[str, Any] = {
    "id": "RS-01",
    "ru": "RU-01",
    "block": "B1",
    "area": "domain",
    "title": "Process holds its steps",
    "acceptance": ["First criterion", "Second criterion"],
}
REFINED: dict[str, Any] = {
    "id": "RS-02",
    "ru": "RU-01",
    "block": "B12",
    "area": "ui",
    "kind": "story",
    "title": "Process list",
    "as_a": "maintainer",
    "i_want": "a list",
    "so_that": "I find things",
    "points": 5,
    "priority": "must",
    "rank": 1,
    "criteria": [{"given": "two processes", "when": "I open the list", "then": "both show"}],
}
MILESTONE = "B1 Domain and metrics"


def test_user_story_reads_as_who_what_why_with_the_right_article() -> None:
    assert user_story(EPICS["RU-01"]) == (
        "As an operations lead, I want to map a process, so that I can analyse it."
    )
    assert user_story(REFINED).startswith("As a maintainer, I want a list")


def test_criteria_read_as_given_when_then_or_as_the_original_list() -> None:
    assert criteria_lines(REFINED) == ["Given two processes, when I open the list, then both show"]
    assert criteria_lines(DELIVERED) == ["First criterion", "Second criterion"]


def test_delivered_item_body_names_epic_release_and_criteria() -> None:
    body = issue_body(DELIVERED, EPICS)
    assert "**Epic:** RU-01 Process modelling: As an operations lead" in body
    assert "**Release:** B1" in body
    assert "### User story" not in body
    assert "- [ ] First criterion" in body


def test_refined_story_body_shows_story_points_and_priority() -> None:
    body = issue_body(REFINED, EPICS)
    assert body.startswith("**Requirement:** RS-02 (story, 5 points, Must)")
    assert "### User story\n\nAs a maintainer, I want a list, so that I find things." in body
    assert "- [ ] Given two processes, when I open the list, then both show" in body


def test_sync_keeps_ticked_criteria_ticked() -> None:
    old = "**User requirement:** RU-01: old text\n\n- [x] First criterion\n- [ ] Second criterion"
    body = issue_body(DELIVERED, EPICS, ticked_criteria(old))
    assert "- [x] First criterion" in body
    assert "- [ ] Second criterion" in body


def test_labels_cover_area_and_priority_when_refined() -> None:
    assert issue_labels(DELIVERED) == {"area:domain"}
    assert issue_labels(REFINED) == {"area:ui", "priority:must"}


def test_an_issue_in_line_with_the_file_needs_no_edit() -> None:
    body = issue_body(DELIVERED, EPICS)
    issue = {
        "title": "RS-01: Process holds its steps",
        "body": body.replace("\n", "\r\n"),
        "milestone": {"title": MILESTONE},
        "labels": [{"name": "req"}, {"name": "area:domain"}],
    }
    assert issue_edits(DELIVERED, body, MILESTONE, issue) == []


def test_a_stale_issue_gets_title_body_milestone_and_labels_fixed() -> None:
    body = issue_body(REFINED, EPICS)
    issue = {
        "title": "RS-02: Old title",
        "body": "old body",
        "milestone": None,
        "labels": [{"name": "req"}, {"name": "area:infra"}, {"name": "priority:could"}],
    }
    assert issue_edits(REFINED, body, MILESTONE, issue) == [
        "--title",
        "RS-02: Process list",
        "--body",
        body,
        "--milestone",
        MILESTONE,
        "--add-label",
        "area:ui",
        "--add-label",
        "priority:must",
        "--remove-label",
        "area:infra",
        "--remove-label",
        "priority:could",
    ]
