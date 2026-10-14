"""Post a checklist on a pull request for the areas its changed files touch.

The checklist is a guide, not a gate: required checks block what CI can verify, and this
lists what a reviewer has to judge. Areas and items live in .github/pr-checklist.toml.
Run by .github/workflows/pr-checklist.yml; locally, print the comment with --dry-run:

    uv run python scripts/pr_checklist.py --repo OWNER/NAME --pr 85 --dry-run
"""

import argparse
import json
import re
import subprocess
import sys
import tomllib
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / ".github" / "pr-checklist.toml"
MARKER = "<!-- pr-checklist -->"
BOT = "github-actions[bot]"
INTRO = (
    "A guide, not a gate: required checks already block what CI can verify. "
    "Tick what you checked, and write *n/a* next to what does not apply."
)

_TYPE = re.compile(r"^(\w+)(\([^)]*\))?!?:")
_CHECKED = re.compile(r"^- \[[xX]\] (.+?)<br>")


@dataclass(frozen=True, slots=True)
class Item:
    text: str
    why: str
    ref: str


@dataclass(frozen=True, slots=True)
class Area:
    title: str
    paths: tuple[str, ...]
    items: tuple[Item, ...]


@dataclass(frozen=True, slots=True)
class Config:
    always: Area
    areas: tuple[Area, ...]
    verification: dict[str, list[str]]


def load_config(path: Path = CONFIG) -> Config:
    data = tomllib.loads(path.read_text(encoding="utf-8"))
    return Config(
        always=_area(data["always"]),
        areas=tuple(_area(area) for area in data["area"]),
        verification=data["verification"],
    )


def _area(data: dict[str, Any]) -> Area:
    return Area(
        title=data["title"],
        paths=tuple(data.get("paths", ())),
        items=tuple(Item(**item) for item in data["item"]),
    )


def pr_type(title: str) -> str | None:
    """`feat(web)!: add x` -> `feat`; None when the title is not a Conventional Commit."""
    match = _TYPE.match(title.strip())
    return match.group(1) if match else None


def matching_areas(config: Config, files: Iterable[str]) -> list[Area]:
    """Areas with at least one changed file under their paths, in config order."""
    changed = list(files)
    return [
        area
        for area in config.areas
        if any(file.startswith(path) for path in area.paths for file in changed)
    ]


def checked_items(body: str) -> set[str]:
    """Item texts already ticked in a previous version of the comment."""
    found = set()
    for line in body.splitlines():
        match = _CHECKED.match(line.strip())
        if match:
            found.add(match.group(1))
    return found


def render(config: Config, files: Iterable[str], title: str, repo: str, checked: set[str]) -> str:
    areas = matching_areas(config, files)
    kind = pr_type(title)
    questions = config.verification.get(kind or "", config.verification["default"])
    touched = ", ".join(area.title for area in areas) or "none of the listed areas"

    lines = [
        MARKER,
        "### Pull request checklist",
        "",
        INTRO,
        "",
        f"**Areas touched:** {touched}",
        "",
        f"#### How it was verified ({f'`{kind}`' if kind else 'any change'})",
        "",
        "Answer these in the description:",
        "",
        *[f"- {question}" for question in questions],
    ]
    for area in (config.always, *areas):
        lines += ["", f"#### {area.title}", ""]
        lines += [_item_line(item, repo, checked) for item in area.items]
    return "\n".join(lines) + "\n"


def _item_line(item: Item, repo: str, checked: set[str]) -> str:
    box = "x" if item.text in checked else " "
    return f"- [{box}] {item.text}<br><sub>Why: {item.why} See {_link(item.ref, repo)}.</sub>"


def _link(ref: str, repo: str) -> str:
    if ref.startswith("https://"):
        return f"[GitHub docs]({ref})"
    return f"[{ref}](https://github.com/{repo}/blob/main/{ref})"


# I/O: everything below talks to GitHub through the gh CLI.


def gh(*args: str, body: dict[str, Any] | None = None) -> str:
    try:
        result = subprocess.run(
            ["gh", *args],
            input=json.dumps(body) if body is not None else None,
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError:
        raise SystemExit("gh CLI not found. Install it and run `gh auth login`.") from None
    if result.returncode != 0:
        raise SystemExit(f"gh {' '.join(args)} failed:\n{result.stderr}")
    return result.stdout


def changed_files(repo: str, pr: int) -> list[str]:
    """Current paths plus the old path of renamed files, so a move out of an area counts."""
    out = gh(
        "api",
        "--paginate",
        f"repos/{repo}/pulls/{pr}/files",
        "--jq",
        ".[] | .filename, (.previous_filename // empty)",
    )
    return out.split()


def existing_comment(repo: str, pr: int) -> tuple[int, str] | None:
    out = gh(
        "api",
        "--paginate",
        f"repos/{repo}/issues/{pr}/comments",
        "--jq",
        ".[] | [.id, .user.login, .body] | @json",
    )
    for line in out.splitlines():
        comment_id, author, body = json.loads(line)
        if author == BOT and body.startswith(MARKER):
            return comment_id, body
    return None


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", required=True, help="OWNER/NAME")
    parser.add_argument("--pr", required=True, type=int)
    parser.add_argument("--dry-run", action="store_true", help="Print the comment only")
    args = parser.parse_args()

    title = json.loads(gh("api", f"repos/{args.repo}/pulls/{args.pr}"))["title"]
    previous = existing_comment(args.repo, args.pr)
    checked = checked_items(previous[1]) if previous else set()
    body = render(load_config(), changed_files(args.repo, args.pr), title, args.repo, checked)

    if args.dry_run:
        sys.stdout.write(body)
    elif previous is None:
        gh(
            "api",
            "-X",
            "POST",
            f"repos/{args.repo}/issues/{args.pr}/comments",
            "--input",
            "-",
            body={"body": body},
        )
    elif previous[1].replace("\r\n", "\n") != body:
        gh(
            "api",
            "-X",
            "PATCH",
            f"repos/{args.repo}/issues/comments/{previous[0]}",
            "--input",
            "-",
            body={"body": body},
        )


if __name__ == "__main__":
    main()
