"""CI runs the slow jobs only when the change can affect them (RS-123, ADR 0023)."""

import re
import subprocess
from pathlib import Path

import pytest
from scripts.ci_changes import changed_files, classify, outputs

ROOT = Path(__file__).resolve().parents[2]
CI = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")

DOCS = [
    "README.md",
    "src/app/domain/CLAUDE.md",
    "docs/adr/0001-deterministic-first-analysis.md",
    "docs/requirements.toml",
    ".github/pull_request_template.md",
    ".github/ISSUE_TEMPLATE/bug.yml",
    ".github/pr-checklist.toml",
    "LICENSE",
]
NOTHING = {"frontend": False, "postgres": False, "stack": False}
EVERYTHING = {"frontend": True, "postgres": True, "stack": True}


def _jobs() -> dict[str, str]:
    """Each job id of ci.yml with its own block of text."""
    blocks = re.split(r"^  (?=[a-z][\w-]*:\s*$)", CI.split("\njobs:\n", 1)[1], flags=re.MULTILINE)
    return {block.split(":", 1)[0]: block for block in blocks if block.strip()}


@pytest.mark.req("RS-123", criterion=1)
@pytest.mark.parametrize("path", DOCS)
def test_a_documentation_file_needs_none_of_the_slow_jobs(path: str) -> None:
    assert classify([path]) == NOTHING


@pytest.mark.req("RS-123", criterion=1)
def test_a_change_of_documentation_only_needs_none_of_the_slow_jobs() -> None:
    assert classify(DOCS) == NOTHING


@pytest.mark.req("RS-123", criterion=1)
@pytest.mark.parametrize("job", ["quality", "test"])
def test_the_fast_jobs_never_carry_a_condition(job: str) -> None:
    assert "\n    if:" not in _jobs()[job]


@pytest.mark.req("RS-123", criterion=1)
@pytest.mark.parametrize("job", ["frontend", "test-postgres", "docker", "e2e"])
def test_each_slow_job_waits_for_the_classification(job: str) -> None:
    assert "\n    needs: changes\n" in _jobs()[job]


@pytest.mark.req("RS-123", criterion=2)
def test_a_change_of_unit_tests_only_needs_none_of_the_slow_jobs() -> None:
    assert classify(["tests/unit/domain/test_scoring.py", "tests/factories.py"]) == NOTHING


@pytest.mark.req("RS-123", criterion=2)
def test_a_change_of_integration_tests_needs_postgres_and_not_the_stack() -> None:
    result = classify(["tests/integration/api/test_processes.py"])
    assert result == {"frontend": False, "postgres": True, "stack": False}


@pytest.mark.req("RS-123", criterion=3)
@pytest.mark.parametrize(
    "path",
    [
        "src/app/api/processes.py",
        "src/app/catalog/insurance.json",
        "Dockerfile",
        "compose.yaml",
        "deploy/nginx/apd-routes.conf",
        "scripts/export_openapi.py",
        ".github/workflows/release.yml",
        "a-file-nobody-knows.txt",
    ],
)
def test_a_file_outside_documentation_and_tests_needs_the_stack(path: str) -> None:
    assert classify([path])["stack"] is True


@pytest.mark.req("RS-123", criterion=3)
def test_one_source_file_among_documentation_still_needs_the_stack() -> None:
    assert classify([*DOCS, "src/app/main.py"])["stack"] is True


@pytest.mark.req("RS-123", criterion=3)
@pytest.mark.parametrize("path", ["src/app/main.py", "alembic.ini", "pyproject.toml", "uv.lock"])
def test_a_change_to_the_api_or_its_dependencies_needs_postgres(path: str) -> None:
    assert classify([path])["postgres"] is True


@pytest.mark.req("RS-123", criterion=3)
@pytest.mark.parametrize("job", ["frontend", "test-postgres", "docker", "e2e"])
def test_each_slow_job_runs_when_the_classification_fails(job: str) -> None:
    assert "!cancelled() && " in _jobs()[job]
    assert "needs.changes.result != 'success' ||" in _jobs()[job]


@pytest.mark.req("RS-123", criterion=3)
def test_a_change_of_the_api_alone_does_not_need_the_frontend_job() -> None:
    assert classify(["src/app/domain/scoring.py"])["frontend"] is False


@pytest.mark.req("RS-123", criterion=4)
@pytest.mark.parametrize("path", ["frontend/src/app/page.tsx", "frontend/e2e/home.spec.ts"])
def test_a_change_in_the_frontend_needs_the_frontend_job_and_the_stack(path: str) -> None:
    assert classify([path]) == {"frontend": True, "postgres": False, "stack": True}


@pytest.mark.req("RS-123", criterion=4)
def test_a_change_of_the_api_contract_needs_the_frontend_job() -> None:
    assert classify(["openapi.json"])["frontend"] is True


@pytest.mark.req("RS-123", criterion=5)
def test_a_change_to_the_ci_workflow_needs_every_job() -> None:
    assert classify([".github/workflows/ci.yml"]) == EVERYTHING


@pytest.mark.req("RS-123", criterion=5)
def test_an_empty_list_of_changes_needs_every_job() -> None:
    assert classify([]) == EVERYTHING


@pytest.mark.req("RS-123", criterion=5)
@pytest.mark.parametrize("job", ["frontend", "test-postgres", "docker", "e2e"])
def test_each_slow_job_runs_on_anything_but_a_pull_request(job: str) -> None:
    assert "github.event_name != 'pull_request' ||" in _jobs()[job]


@pytest.mark.req("RS-123", criterion=5)
def test_no_job_with_a_matrix_carries_a_condition() -> None:
    with_matrix = [job for job, text in _jobs().items() if "matrix:" in text]
    assert with_matrix == ["test"]
    assert all("\n    if:" not in _jobs()[job] for job in with_matrix)


@pytest.mark.req("RS-123", criterion=5)
def test_the_workflow_filters_no_paths() -> None:
    assert "paths:" not in CI
    assert "paths-ignore:" not in CI


def test_the_outputs_are_one_github_output_line_per_job_group() -> None:
    assert outputs({"frontend": True, "postgres": False, "stack": True}) == (
        "frontend=true\npostgres=false\nstack=true\n"
    )


@pytest.mark.req("RS-123", criterion=2)
@pytest.mark.parametrize("path", ["tests/payloads.py", "tests/snapshots/invoice-approval.json"])
def test_a_helper_the_integration_tests_read_needs_postgres_and_not_the_stack(path: str) -> None:
    assert classify([path]) == {"frontend": False, "postgres": True, "stack": False}


def _git(repo: Path, *args: str) -> str:
    done = subprocess.run(
        ["git", "-c", "user.name=ci", "-c", "user.email=ci@example.com", *args],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    )
    return done.stdout.strip()


@pytest.mark.req("RS-123", criterion=2)
def test_a_moved_file_counts_where_it_came_from(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _git(tmp_path, "init", "--quiet")
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "catalog.json").write_text('{"sector": "insurance"}\n', encoding="utf-8")
    _git(tmp_path, "add", ".")
    _git(tmp_path, "commit", "--quiet", "-m", "base")
    base = _git(tmp_path, "rev-parse", "HEAD")
    (tmp_path / "docs").mkdir()
    _git(tmp_path, "mv", "src/catalog.json", "docs/catalog.json")
    _git(tmp_path, "commit", "--quiet", "-m", "move")
    head = _git(tmp_path, "rev-parse", "HEAD")
    monkeypatch.chdir(tmp_path)

    assert sorted(changed_files(base, head)) == ["docs/catalog.json", "src/catalog.json"]
