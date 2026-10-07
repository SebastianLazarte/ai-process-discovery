"""Architecture boundaries, enforced as tests (RS-08, RS-26, RS-42)."""

import ast
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src" / "app"


def _imports(directory: Path) -> dict[Path, set[str]]:
    found: dict[Path, set[str]] = {}
    for path in directory.rglob("*.py"):
        modules: set[str] = set()
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if isinstance(node, ast.Import):
                modules.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
                modules.add(node.module)
        found[path] = modules
    return found


def _violations(directory: Path, forbidden: tuple[str, ...]) -> list[str]:
    return [
        f"{path.relative_to(ROOT)} imports {module}"
        for path, modules in _imports(directory).items()
        for module in modules
        if module.split(".")[0] in forbidden or module.startswith(forbidden)
    ]


@pytest.mark.parametrize(
    ("directory", "forbidden"),
    [
        (
            SRC / "domain",
            (
                "fastapi",
                "sqlalchemy",
                "anthropic",
                "streamlit",
                "httpx",
                "pydantic",
                "app.llm",
                "app.models",
                "app.repositories",
                "app.services",
                "app.api",
            ),
        ),
        (SRC / "services", ("anthropic", "streamlit", "fastapi")),
        (ROOT / "ui", ("app",)),
    ],
)
def test_layer_does_not_import_forbidden_modules(
    directory: Path, forbidden: tuple[str, ...]
) -> None:
    assert directory.exists(), directory
    assert _violations(directory, forbidden) == []


def test_no_print_calls_in_source() -> None:
    offenders = [
        str(path.relative_to(ROOT))
        for path in SRC.rglob("*.py")
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8")))
        if isinstance(node, ast.Call) and getattr(node.func, "id", None) == "print"
    ]
    assert offenders == []
