"""Decide which slow CI jobs a pull request needs, from the files it changes (RS-123, ADR 0023).

Run by the `changes` job of .github/workflows/ci.yml with plain `python3`, so it uses the
standard library only. It writes `frontend`, `postgres` and `stack` to `$GITHUB_OUTPUT`;
`frontend`, `test-postgres`, `docker` and `e2e` read them on pull requests and run every
time on `main`. A file it does not know needs the whole stack, and so does an empty list.

    python3 scripts/ci_changes.py <base-sha> <head-sha>
"""

import os
import subprocess
import sys
from collections.abc import Iterable

CI_WORKFLOW = ".github/workflows/ci.yml"
DOCS_FILES = frozenset({".github/pr-checklist.toml", "LICENSE"})
DOCS_PREFIXES = ("docs/", ".github/ISSUE_TEMPLATE/")
FRONTEND_PREFIXES = ("frontend/",)
FRONTEND_FILES = frozenset({"openapi.json", CI_WORKFLOW})
POSTGRES_PREFIXES = ("src/", "tests/integration/")
POSTGRES_FILES = frozenset({"alembic.ini", "pyproject.toml", "uv.lock", CI_WORKFLOW})


def _is_docs(path: str) -> bool:
    return path.endswith(".md") or path in DOCS_FILES or path.startswith(DOCS_PREFIXES)


def _is_python_test(path: str) -> bool:
    return path.startswith("tests/")


def classify(paths: Iterable[str]) -> dict[str, bool]:
    """Which job groups the changed files need: `frontend`, `postgres` and `stack`."""
    changed = list(paths)
    if not changed:
        return {"frontend": True, "postgres": True, "stack": True}
    code = [p for p in changed if not _is_docs(p)]
    return {
        "frontend": any(p.startswith(FRONTEND_PREFIXES) or p in FRONTEND_FILES for p in code),
        "postgres": any(p.startswith(POSTGRES_PREFIXES) or p in POSTGRES_FILES for p in code),
        "stack": any(not _is_python_test(p) for p in code),
    }


def outputs(needs: dict[str, bool]) -> str:
    """The `$GITHUB_OUTPUT` lines for each job group."""
    return "".join(f"{name}={str(value).lower()}\n" for name, value in needs.items())


def changed_files(base: str, head: str) -> list[str]:
    diff = subprocess.run(
        ["git", "diff", "--name-only", f"{base}...{head}"],
        check=True,
        capture_output=True,
        text=True,
    )
    return [line for line in diff.stdout.splitlines() if line]


def main() -> None:
    base, head = sys.argv[1:3]
    paths = changed_files(base, head)
    text = outputs(classify(paths))
    sys.stdout.write("\n".join(paths) + "\n\n" + text)
    with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as output:
        output.write(text)


if __name__ == "__main__":
    main()
