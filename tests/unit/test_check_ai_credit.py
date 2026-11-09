"""Hard rule 8 as a check (ADR 0022): Claude may be credited only by one exact co-author line."""

import sys
from pathlib import Path

import pytest
from scripts import check_ai_credit
from scripts.check_ai_credit import SCISSORS, commit_message, credited_lines, findings

CO_AUTHOR = "Co-Authored-By: Claude <noreply@anthropic.com>"
WITH_MODEL = "Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>"
FOOTER = "🤖 Generated with [Claude Code](https://claude.com/claude-code)"
RELEASE_BODY = (
    "This PR was generated with [Release Please](https://github.com/googleapis/release-please).\n"
    "Co-authored-by: github-actions[bot] <41898282+github-actions[bot]@users.noreply.github.com>"
)


@pytest.mark.parametrize(
    "line",
    [
        WITH_MODEL,
        WITH_MODEL.lower(),
        "co-authored-by:claude",
        "Co-Authored-By: Claude <claude@example.com>",
        f"{CO_AUTHOR} (claude-opus-4-5)",
        FOOTER,
        "generated with claude code",
        "Signed-off-by: someone <noreply@anthropic.com>",
    ],
)
def test_any_other_form_of_credit_is_found_whatever_the_case(line: str) -> None:
    assert credited_lines(f"feat: x\n\n{line}\n") == [line]


@pytest.mark.parametrize("line", [CO_AUTHOR, CO_AUTHOR.lower(), f"  {CO_AUTHOR}  "])
def test_the_plain_co_author_line_is_allowed(line: str) -> None:
    assert credited_lines(f"feat: x\n\n{line}\n") == []


@pytest.mark.parametrize(
    "text",
    [
        RELEASE_BODY,
        "`uv.lock` was regenerated with `uv add`.",
        "feat(api): x\n\nCo-authored-by: Sebastian <sebastian@example.com>",
        "Claude reviewed nothing here.",
    ],
)
def test_release_bots_people_and_plain_mentions_pass(text: str) -> None:
    assert credited_lines(text) == []


def test_comment_lines_and_the_diff_below_the_scissors_are_not_the_message() -> None:
    raw = f"feat: x\n# {FOOTER}\n{SCISSORS}\n+{FOOTER}\n"
    assert commit_message(raw) == "feat: x"


def test_each_finding_names_where_the_credit_is() -> None:
    sources = [("pull request body", f"Done.\n{FOOTER}"), ("commit abc1234", "fix: y")]
    assert findings(sources) == [f"pull request body: {FOOTER}"]


def run(monkeypatch: pytest.MonkeyPatch, *args: str) -> None:
    monkeypatch.setattr(sys, "argv", ["check_ai_credit.py", *args])
    check_ai_credit.main()


def test_a_commit_that_names_the_model_is_rejected(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    message = tmp_path / "COMMIT_EDITMSG"
    message.write_text(f"feat: x\n\n{WITH_MODEL}\n", encoding="utf-8")
    with pytest.raises(SystemExit) as error:
        run(monkeypatch, "--message-file", str(message))
    assert f"commit message: {WITH_MODEL}" in str(error.value.code)


@pytest.mark.parametrize("body", ["Body.", f"Body.\n\n{CO_AUTHOR}"])
def test_a_clean_or_co_authored_commit_passes(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, body: str
) -> None:
    message = tmp_path / "COMMIT_EDITMSG"
    message.write_text(f"feat: x\n\n{body}\n", encoding="utf-8")
    run(monkeypatch, "--message-file", str(message))


def test_a_pull_request_fails_on_a_footer_in_any_commit(monkeypatch: pytest.MonkeyPatch) -> None:
    sources = [("pull request body", "Done."), ("commit abc1234", f"fix: y\n\n{FOOTER}")]
    monkeypatch.setattr(check_ai_credit, "fetch_pr", lambda repo, pr: sources)
    with pytest.raises(SystemExit) as error:
        run(monkeypatch, "--repo", "owner/name", "--pr", "7")
    assert f"commit abc1234: {FOOTER}" in str(error.value.code)


def test_a_co_authored_pull_request_passes(monkeypatch: pytest.MonkeyPatch) -> None:
    sources = [("pull request body", "Done."), ("commit abc1234", f"fix: y\n\n{CO_AUTHOR}")]
    monkeypatch.setattr(check_ai_credit, "fetch_pr", lambda repo, pr: sources)
    run(monkeypatch, "--repo", "owner/name", "--pr", "7")


def test_a_release_pull_request_passes(monkeypatch: pytest.MonkeyPatch) -> None:
    sources = [("pull request body", RELEASE_BODY), ("commit abc1234", "chore(release): 2.0.0")]
    monkeypatch.setattr(check_ai_credit, "fetch_pr", lambda repo, pr: sources)
    run(monkeypatch, "--repo", "owner/name", "--pr", "7")


def test_a_pull_request_number_needs_the_repository(monkeypatch: pytest.MonkeyPatch) -> None:
    with pytest.raises(SystemExit) as error:
        run(monkeypatch, "--pr", "7")
    assert error.value.code == 2
