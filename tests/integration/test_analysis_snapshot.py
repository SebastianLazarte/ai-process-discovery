"""Characterization tests: the full output for each demo process, frozen (RS-82).

They pin what the analysis services produce today, so a refactor that changes any figure,
risk, note or blueprint line fails here. Ids and timestamps are replaced by stable
placeholders. After an intended change of behaviour, regenerate and review the diff:

    UPDATE_SNAPSHOTS=1 uv run pytest tests/integration/test_analysis_snapshot.py
"""

import json
import os
import re
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

SNAPSHOTS = Path(__file__).resolve().parents[1] / "snapshots"
DEMOS = ("bank-reconciliation", "customer-onboarding", "invoice-intake")

_UUID = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}")
_TIMESTAMP = re.compile(r"\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}(\.\d+)?(Z|[+-]\d{2}:\d{2})?")


def normalise(observed: dict[str, Any], names: dict[str, str]) -> str:
    """Name each known id by its role, any other id by order, and hide timestamps.

    Ids are replaced before keys are sorted, so the order never depends on random UUIDs.
    """
    others: dict[str, str] = {}

    def placeholder(match: re.Match[str]) -> str:
        found = match.group()
        return names.get(found) or others.setdefault(found, f"<other-{len(others) + 1}>")

    text = _TIMESTAMP.sub("<timestamp>", _UUID.sub(placeholder, json.dumps(observed)))
    return json.dumps(json.loads(text), indent=2, sort_keys=True) + "\n"


def _ok(response: Any, status: int = 200) -> Any:
    assert response.status_code == status, response.text
    return response


def _observe(client: TestClient, slug: str) -> tuple[dict[str, Any], dict[str, str]]:
    process = _ok(client.post(f"/demo-processes/{slug}"), 201).json()
    steps = process["steps"]
    analysis = _ok(
        client.post(
            f"/processes/{process['id']}/analyses",
            json={
                "use_llm": True,
                "confirm_sensitive": True,
                "assumptions": {
                    "implementation_cost": "6000",
                    "monthly_tooling_cost": "50",
                    "expected_time_reduction_by_step": {s["id"]: "0.5" for s in steps[:-1]},
                },
            },
        ),
        201,
    ).json()
    reviewed = _ok(
        client.post(
            f"/analyses/{analysis['id']}/overrides",
            json={
                "step_id": steps[0]["id"],
                "method": "MANUAL",
                "human_control": "REQUIRED",
                "reason": "Reviewer keeps this step manual",
            },
        ),
        201,
    ).json()
    names = {process["id"]: "<process>", analysis["id"]: "<analysis>"}
    names.update({s["id"]: f"<step-{s['position']}>" for s in steps})
    names.update(
        {s["override"]["id"]: "<override>" for s in reviewed["step_assessments"] if s["override"]}
    )
    observed = {
        "analysis": analysis,
        "reviewed": reviewed,
        "history": _ok(client.get(f"/processes/{process['id']}/analyses")).json(),
        "blueprint_md": _ok(client.get(f"/analyses/{analysis['id']}/blueprint.md")).text,
    }
    return observed, names


@pytest.mark.parametrize("slug", DEMOS)
def test_analysis_output_matches_the_snapshot(client: TestClient, slug: str) -> None:
    observed = normalise(*_observe(client, slug))
    path = SNAPSHOTS / f"{slug}.json"
    if os.environ.get("UPDATE_SNAPSHOTS") == "1":
        path.parent.mkdir(exist_ok=True)
        path.write_text(observed, encoding="utf-8")
    assert observed == path.read_text(encoding="utf-8")


def test_normalise_names_ids_by_role_and_hides_timestamps() -> None:
    known, other = "0b7f6a1e-1c2d-4e5f-8a9b-0c1d2e3f4a5b", "1c8a7b2f-2d3e-4f50-9b0c-1d2e3f4a5b6c"
    observed = {"a": [known, other, known], "at": "2026-10-16T09:30:00.123456Z", known: 1}
    assert json.loads(normalise(observed, {known: "<step-1>"})) == {
        "a": ["<step-1>", "<other-1>", "<step-1>"],
        "at": "<timestamp>",
        "<step-1>": 1,
    }
