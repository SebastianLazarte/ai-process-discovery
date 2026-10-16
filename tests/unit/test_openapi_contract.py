"""RS-69: the committed contract is the one the API serves, so the frontend types never drift."""

import json

import pytest
from scripts.export_openapi import CONTRACT, CONTRACT_VERSION, contract

import app.main
from app.core.config import Settings


def test_committed_contract_matches_the_app() -> None:
    assert CONTRACT.read_text(encoding="utf-8") == contract(), (
        "frontend/openapi.json is stale: run `uv run python scripts/export_openapi.py`"
    )


def test_contract_documents_paths_relative_to_the_api_prefix() -> None:
    schema = json.loads(contract())
    assert schema["servers"] == [{"url": "/api"}]
    assert "/processes" in schema["paths"]
    assert not any(path.startswith("/api/") for path in schema["paths"])


def test_contract_does_not_change_with_the_release_version(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # A release bump must not make the committed contract stale (release PR 1.4.0).
    before = contract()
    monkeypatch.setattr(app.main, "__version__", "99.0.0")
    served = app.main.create_app(Settings(database_url="sqlite://", log_level="WARNING")).openapi()
    assert served["info"]["version"] == "99.0.0"
    assert contract() == before
    assert json.loads(before)["info"]["version"] == CONTRACT_VERSION
