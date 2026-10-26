"""Requirement traceability: which tests prove which backlog item (ADR 0012, RS-103).

Python tests carry a marker, on the test, on its class or as the module's ``pytestmark``:

    @pytest.mark.req("RS-63")                # the item as a whole
    @pytest.mark.req("RS-63", criterion=2)   # one Given/When/Then criterion

Frontend tests (Vitest and Playwright) put the id at the start of a test or describe title:
``"RS-74: ..."``, or ``"RS-74.2: ..."`` for criterion 2.

    uv run python scripts/traceability.py    # the matrix as Markdown, for the CI job summary
"""

import ast
import re
import sys
import tomllib
from collections import defaultdict
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REQUIREMENTS = ROOT / "docs" / "requirements.toml"

FRONTEND_TITLE = re.compile(
    r"""\b(?:describe|it|test)(?:\.\w+)*\(\s*["'`](RS-\d+)(?:\.(\d+))?:""",
)


@dataclass(frozen=True)
class Ref:
    item: str
    criterion: int | None
    test: str

    def key(self) -> tuple[str, int, str]:
        """Sort key: an item-level reference (no criterion) comes before the item's criteria."""
        return (self.item, self.criterion or 0, self.test)


def load_requirements(path: Path = REQUIREMENTS) -> dict[str, dict[str, Any]]:
    with path.open("rb") as handle:
        return {r["id"]: r for r in tomllib.load(handle)["requirement"]}


def _req_marks(node: ast.expr) -> list[tuple[str, int | None]]:
    """The (item, criterion) pairs of every ``pytest.mark.req(...)`` call in an expression."""
    found: list[tuple[str, int | None]] = []
    for call in ast.walk(node):
        if not (isinstance(call, ast.Call) and isinstance(call.func, ast.Attribute)):
            continue
        if call.func.attr != "req" or not ast.unparse(call.func).endswith("mark.req"):
            continue
        item = call.args[0].value if call.args and isinstance(call.args[0], ast.Constant) else None
        criterion = next(
            (
                k.value.value
                for k in call.keywords
                if k.arg == "criterion" and isinstance(k.value, ast.Constant)
            ),
            None,
        )
        if isinstance(item, str):
            found.append((item, criterion if isinstance(criterion, int) else None))
    return found


def python_refs(files: Iterable[Path], root: Path = ROOT) -> list[Ref]:
    refs: list[Ref] = []
    for path in files:
        tree = ast.parse(path.read_text(encoding="utf-8"))
        module_marks = [
            mark
            for stmt in tree.body
            if isinstance(stmt, ast.Assign)
            and any(isinstance(t, ast.Name) and t.id == "pytestmark" for t in stmt.targets)
            for mark in _req_marks(stmt.value)
        ]

        def tests_in(
            body: list[ast.stmt], inherited: list[tuple[str, int | None]], prefix: str
        ) -> None:
            for stmt in body:
                if isinstance(stmt, ast.ClassDef):
                    own = [m for d in stmt.decorator_list for m in _req_marks(d)]
                    tests_in(stmt.body, inherited + own, f"{prefix}{stmt.name}::")
                elif isinstance(
                    stmt, ast.FunctionDef | ast.AsyncFunctionDef
                ) and stmt.name.startswith("test"):
                    marks = inherited + [m for d in stmt.decorator_list for m in _req_marks(d)]
                    refs.extend(Ref(item, crit, f"{prefix}{stmt.name}") for item, crit in marks)

        tests_in(tree.body, module_marks, f"{path.relative_to(root).as_posix()}::")
    return refs


def frontend_refs(files: Iterable[Path], root: Path = ROOT) -> list[Ref]:
    refs: list[Ref] = []
    for path in files:
        name = path.relative_to(root).as_posix()
        for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            for match in FRONTEND_TITLE.finditer(line):
                criterion = int(match.group(2)) if match.group(2) else None
                refs.append(Ref(match.group(1), criterion, f"{name}:{line_no}"))
    return refs


def collect(root: Path = ROOT) -> list[Ref]:
    python = sorted((root / "tests").rglob("test_*.py"))
    frontend = sorted((root / "frontend" / "src").rglob("*.test.ts*")) + sorted(
        (root / "frontend" / "e2e").rglob("*.spec.ts")
    )
    return sorted(python_refs(python, root) + frontend_refs(frontend, root), key=Ref.key)


def _criteria_count(requirement: dict[str, Any]) -> int:
    return len(requirement.get("criteria") or requirement.get("acceptance") or [])


def problems(
    requirements: dict[str, dict[str, Any]], refs: Sequence[Ref], released_blocks: Iterable[str]
) -> list[str]:
    """Every reference names an existing item and criterion; every released item has a test."""
    found: list[str] = []
    for ref in refs:
        requirement = requirements.get(ref.item)
        if requirement is None:
            found.append(f"{ref.test}: unknown item {ref.item}")
        elif ref.criterion is not None and not 1 <= ref.criterion <= _criteria_count(requirement):
            found.append(f"{ref.test}: {ref.item} has no criterion {ref.criterion}")
    covered = {ref.item for ref in refs}
    blocks = set(released_blocks)
    for item, requirement in requirements.items():
        if requirement["block"] in blocks and item not in covered:
            found.append(f"{item} ({requirement['block']}) has no test")
    return sorted(found)


def _number(item: str) -> int:
    return int(item.split("-")[1])


def matrix(requirements: dict[str, dict[str, Any]], refs: Sequence[Ref]) -> str:
    rows: dict[tuple[str, int | None], list[str]] = defaultdict(list)
    for ref in refs:
        rows[(ref.item, ref.criterion)].append(ref.test)
    covered = len({item for item, _ in rows})
    lines = [
        "## Requirement traceability",
        "",
        f"{covered} of {len(requirements)} backlog items have a marked test "
        f"({len(refs)} references).",
        "",
        "| Item | Block | Criterion | Tests |",
        "|---|---|---|---|",
    ]
    for (item, criterion), tests in sorted(
        rows.items(), key=lambda kv: (_number(kv[0][0]), kv[0][1] or 0)
    ):
        block = requirements.get(item, {}).get("block", "?")
        listed = "<br>".join(f"`{t}`" for t in sorted(tests))
        lines.append(f"| {item} | {block} | {criterion if criterion else 'item'} | {listed} |")
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    del argv
    sys.stdout.write(matrix(load_requirements(), collect()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
