"""Fail when a commit message or a pull request credits an AI assistant (hard rule 8).

Commits and pull requests are authored by the maintainer only. The squash commit on main
takes the pull request body, so CI checks the body as well as every commit. Two modes:

    uv run python scripts/check_ai_credit.py --message-file .git/COMMIT_EDITMSG
    uv run python scripts/check_ai_credit.py --repo OWNER/NAME --pr 85

The first runs as the commit-msg hook of .pre-commit-config.yaml, the second in the
pr-title job of .github/workflows/pr-title.yml.
"""

import argparse
import json
import re
import subprocess
from collections.abc import Iterable
from pathlib import Path

# Same pattern as the maintainer's agent hook. It names the assistant on purpose: release
# pull requests say "generated with Release Please" and credit github-actions[bot].
CREDIT = re.compile(
    r"co-authored-by:\s*claude|noreply@anthropic\.com|generated with \[?claude code",
    re.IGNORECASE,
)
SCISSORS = "# ------------------------ >8 ------------------------"


def credited_lines(text: str) -> list[str]:
    return [line.strip() for line in text.splitlines() if CREDIT.search(line)]


def commit_message(raw: str) -> str:
    """What git keeps from the message file: no comment lines, nothing below the scissors."""
    kept = raw.split(SCISSORS, 1)[0]
    return "\n".join(line for line in kept.splitlines() if not line.startswith("#"))


def findings(sources: Iterable[tuple[str, str]]) -> list[str]:
    """One `where: line` entry per credit, from (where, text) pairs."""
    return [f"{where}: {line}" for where, text in sources for line in credited_lines(text)]


def fail_on(found: list[str]) -> None:
    if found:
        raise SystemExit(
            "Hard rule 8: commits and pull requests credit no AI assistant. Remove:\n"
            + "\n".join(f"  {entry}" for entry in found)
        )


# I/O: everything below talks to GitHub through the gh CLI.


def gh(*args: str) -> str:
    try:
        result = subprocess.run(["gh", *args], capture_output=True, text=True, check=False)
    except FileNotFoundError:
        raise SystemExit("gh CLI not found. Install it and run `gh auth login`.") from None
    if result.returncode != 0:
        raise SystemExit(f"gh {' '.join(args)} failed:\n{result.stderr}")
    return result.stdout


def fetch_pr(repo: str, pr: int) -> list[tuple[str, str]]:
    """The pull request body and every commit message, labelled by where they come from."""
    body = json.loads(gh("api", f"repos/{repo}/pulls/{pr}"))["body"] or ""
    out = gh(
        "api",
        "--paginate",
        f"repos/{repo}/pulls/{pr}/commits",
        "--jq",
        ".[] | [.sha, .commit.message] | @json",
    )
    commits = [json.loads(line) for line in out.splitlines()]
    return [("pull request body", body), *[(f"commit {sha[:7]}", msg) for sha, msg in commits]]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--message-file", type=Path, help="Commit message file (commit-msg)")
    mode.add_argument("--pr", type=int, help="Pull request number, with --repo")
    parser.add_argument("--repo", help="OWNER/NAME")
    args = parser.parse_args()

    if args.message_file is not None:
        raw = args.message_file.read_text(encoding="utf-8")
        fail_on(findings([("commit message", commit_message(raw))]))
    elif args.repo is None:
        parser.error("--pr needs --repo")
    else:
        fail_on(findings(fetch_pr(args.repo, args.pr)))


if __name__ == "__main__":
    main()
