import tomllib
from pathlib import Path

import app


def test_version_comes_from_the_package_metadata() -> None:
    pyproject = Path(__file__).resolve().parents[2] / "pyproject.toml"
    expected = tomllib.loads(pyproject.read_text(encoding="utf-8"))["project"]["version"]
    assert app.__version__ == expected
