"""Requirement traceability (ADR 0012, RS-103).

The checks run on the real repository: every reference names an existing item and
criterion, and every item of a released block has at least one test. A block joins
RELEASED_BLOCKS once all its items carry markers, so the list widens with each backfill.
"""

from pathlib import Path

import pytest
from scripts.traceability import (
    ROOT,
    Ref,
    collect,
    frontend_refs,
    load_requirements,
    main,
    problems,
    python_refs,
)

RELEASED_BLOCKS = ("B11", "B12")

REQUIREMENTS = load_requirements()
REFS = collect()


@pytest.mark.req("RS-103", criterion=1)
def test_every_reference_names_an_existing_item_and_criterion() -> None:
    assert problems(REQUIREMENTS, REFS, released_blocks=()) == []


@pytest.mark.req("RS-103", criterion=1)
def test_an_unknown_item_or_criterion_is_named(tmp_path: Path) -> None:
    test_file = tmp_path / "test_sample.py"
    test_file.write_text(
        "import pytest\n\n"
        '@pytest.mark.req("RS-9999")\n'
        "def test_unknown_item(): ...\n\n"
        '@pytest.mark.req("RS-103", criterion=9)\n'
        "def test_unknown_criterion(): ...\n",
        encoding="utf-8",
    )

    found = problems(REQUIREMENTS, python_refs([test_file], tmp_path), released_blocks=())

    assert found == [
        "test_sample.py::test_unknown_criterion: RS-103 has no criterion 9",
        "test_sample.py::test_unknown_item: unknown item RS-9999",
    ]


@pytest.mark.req("RS-103", criterion=2)
def test_every_item_of_a_released_block_has_a_test() -> None:
    assert problems(REQUIREMENTS, REFS, RELEASED_BLOCKS) == []


@pytest.mark.req("RS-103", criterion=2)
def test_an_untested_item_of_a_released_block_is_named() -> None:
    requirements = {
        "RS-1": {"block": "B1", "criteria": [{}]},
        "RS-2": {"block": "B1", "criteria": [{}]},
        "RS-3": {"block": "B2", "criteria": [{}]},
    }
    refs = [Ref("RS-1", None, "tests/test_a.py::test_a")]

    assert problems(requirements, refs, released_blocks=("B1",)) == ["RS-2 (B1) has no test"]


@pytest.mark.req("RS-103", criterion=2)
def test_markers_reach_tests_from_the_module_class_and_function(tmp_path: Path) -> None:
    test_file = tmp_path / "test_sample.py"
    test_file.write_text(
        "import pytest\n\n"
        'pytestmark = [pytest.mark.skipif(False, reason="x"), pytest.mark.req("RS-1")]\n\n'
        '@pytest.mark.req("RS-2", criterion=1)\n'
        "class TestGroup:\n"
        '    @pytest.mark.req("RS-3")\n'
        "    def test_inside(self): ...\n\n"
        "def test_plain(): ...\n\n"
        "def helper(): ...\n",
        encoding="utf-8",
    )

    refs = sorted(python_refs([test_file], tmp_path), key=Ref.key)

    assert refs == [
        Ref("RS-1", None, "test_sample.py::TestGroup::test_inside"),
        Ref("RS-1", None, "test_sample.py::test_plain"),
        Ref("RS-2", 1, "test_sample.py::TestGroup::test_inside"),
        Ref("RS-3", None, "test_sample.py::TestGroup::test_inside"),
    ]


@pytest.mark.req("RS-103", criterion=2)
def test_frontend_titles_that_start_with_an_id_are_references(tmp_path: Path) -> None:
    spec = tmp_path / "view.test.tsx"
    spec.write_text(
        'describe("RS-74: the steps list", () => {\n'
        '  it("RS-74.2: offers the enum members", () => {});\n'
        '  it("mentions RS-75 later in the title", () => {});\n'
        "});\n"
        'test.skip("RS-91: reorders", async () => {});\n',
        encoding="utf-8",
    )

    assert frontend_refs([spec], tmp_path) == [
        Ref("RS-74", None, "view.test.tsx:1"),
        Ref("RS-74", 2, "view.test.tsx:2"),
        Ref("RS-91", None, "view.test.tsx:5"),
    ]


@pytest.mark.req("RS-103", criterion=3)
def test_the_script_prints_the_matrix(capsys: pytest.CaptureFixture[str]) -> None:
    assert main([]) == 0

    out = capsys.readouterr().out
    assert "| Item | Block | Criterion | Tests |" in out
    assert "| RS-103 | B13 | 1 | " in out
    assert "tests/unit/test_traceability.py::test_the_script_prints_the_matrix" in out


@pytest.mark.req("RS-103", criterion=3)
def test_the_ci_test_job_writes_the_matrix_to_the_summary() -> None:
    workflow = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    assert 'uv run python scripts/traceability.py >> "$GITHUB_STEP_SUMMARY"' in workflow


@pytest.mark.req("RS-103", criterion=4)
def test_the_definition_of_done_asks_for_one_marked_test_per_criterion() -> None:
    docs = (ROOT / "docs" / "CLAUDE.md").read_text(encoding="utf-8")
    done = next(line for line in docs.splitlines() if line.startswith("- **Definition of Done**"))
    assert "one marked test per criterion" in done
