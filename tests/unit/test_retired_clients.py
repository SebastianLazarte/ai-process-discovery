"""RS-80: the vanilla client and Streamlit are gone in 2.0.0, and the docs say so (ADR 0016).

The API side of RS-80 lives in tests/integration/api/test_api_routes.py, and the /ui/ 301 in
tests/unit/test_nginx_routes.py and frontend/e2e/retired-routes.spec.ts.
"""

import re
from pathlib import Path

import pytest
from scripts.bootstrap_github import REQUIRED_CHECKS

from app.core.config import Settings

ROOT = Path(__file__).resolve().parents[2]
WORKFLOWS = ROOT / ".github" / "workflows"


def _job_names(workflow: str) -> set[str]:
    text = (WORKFLOWS / workflow).read_text(encoding="utf-8")
    return set(re.findall(r"^    name: (\S+)\s*$", text, flags=re.MULTILINE))


def _text(name: str) -> str:
    return (ROOT / name).read_text(encoding="utf-8")


# Criterion 1: web/, WEB_FILES and the web check are gone (Streamlit too, by PO decision).


@pytest.mark.parametrize("folder", ["web", "ui"])
def test_the_retired_clients_have_no_folder(folder: str) -> None:
    assert not (ROOT / folder).exists()


def test_the_api_serves_no_client_files() -> None:
    sources = [
        path
        for path in (ROOT / "src").rglob("*.py")
        if "WEB_FILES" in path.read_text(encoding="utf-8")
    ]
    assert sources == []
    assert not (ROOT / "src" / "app" / "api" / "routes" / "web.py").exists()
    assert "web_dir" not in Settings.model_fields


def test_ci_has_no_web_job_and_requires_e2e() -> None:
    jobs = _job_names("ci.yml")
    assert "web" not in jobs
    assert "web" not in REQUIRED_CHECKS
    assert "e2e" in REQUIRED_CHECKS


def test_every_required_check_is_a_job() -> None:
    jobs = _job_names("ci.yml") | _job_names("pr-title.yml")
    assert {re.sub(r" \(.*\)$", "", check) for check in REQUIRED_CHECKS} <= jobs


def test_streamlit_is_no_dependency() -> None:
    assert "streamlit" not in _text("pyproject.toml").lower()
    assert 'name = "streamlit"' not in _text("uv.lock")


# Criterion 4: README, CLAUDE.md and the required checks describe the new layout.

RETIRED = [":8000/ui/", "web/tests", "WEB_FILES", ":3000/app", ":8080/app", "streamlit run", "8501"]


@pytest.mark.parametrize("name", ["README.md", "CLAUDE.md", "CONTRIBUTING.md"])
def test_docs_no_longer_describe_the_retired_layout(name: str) -> None:
    text = _text(name)
    assert [phrase for phrase in RETIRED if phrase in text] == []


def test_readme_opens_the_client_at_the_root_through_the_edge() -> None:
    assert "<http://localhost:8080/>" in _text("README.md")


@pytest.mark.parametrize(
    ("name", "lead"), [("CLAUDE.md", "Required checks:"), ("CONTRIBUTING.md", "must pass:")]
)
def test_docs_list_the_required_checks(name: str, lead: str) -> None:
    line = next(line for line in _text(name).splitlines() if lead in line)
    listed = re.findall(r"`([^`]+)`", line.split(lead, 1)[1])
    assert listed == REQUIRED_CHECKS
