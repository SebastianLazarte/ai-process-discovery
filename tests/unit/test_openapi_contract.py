"""RS-69: the committed contract is the one the API serves, so the frontend types never drift."""

import json

from scripts.export_openapi import CONTRACT, contract


def test_committed_contract_matches_the_app() -> None:
    assert CONTRACT.read_text(encoding="utf-8") == contract(), (
        "frontend/openapi.json is stale: run `uv run python scripts/export_openapi.py`"
    )


def test_contract_documents_paths_relative_to_the_api_prefix() -> None:
    schema = json.loads(contract())
    assert schema["servers"] == [{"url": "/api"}]
    assert "/processes" in schema["paths"]
    assert not any(path.startswith("/api/") for path in schema["paths"])
