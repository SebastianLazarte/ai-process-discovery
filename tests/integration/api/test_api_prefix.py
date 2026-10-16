"""RS-69: the API answers under /api, and at the root until 2.0.0 (ADR 0009)."""

import re

import pytest
from fastapi.testclient import TestClient

MISSING = "00000000-0000-4000-8000-000000000000"


def _operations(client: TestClient) -> list[tuple[str, str]]:
    paths = client.get("/api/openapi.json").json()["paths"]
    return [(method.upper(), path) for path, item in paths.items() for method in item]


def test_every_documented_operation_answers_the_same_under_api_and_at_the_root(
    client: TestClient,
) -> None:
    # Unknown ids and empty bodies, so each call fails the same safe way and changes nothing.
    operations = _operations(client)
    assert len(operations) >= 15, operations
    for method, template in operations:
        path = re.sub(r"\{\w+\}", MISSING, template)
        body = None if method in ("GET", "DELETE") else {}
        prefixed = client.request(method, f"/api{path}", json=body)
        root = client.request(method, path, json=body)
        assert prefixed.status_code == root.status_code, f"{method} {path}"
        assert prefixed.content == root.content, f"{method} {path}"


def test_data_written_under_api_reads_back_at_the_root(client: TestClient) -> None:
    created = client.post(
        "/api/processes", json={"name": "Quote approval", "executions_per_month": 40}
    )
    assert created.status_code == 201, created.text
    assert client.get(f"/processes/{created.json()['id']}").json() == created.json()


@pytest.mark.parametrize("path", ["/api/docs", "/api/redoc", "/api/openapi.json"])
def test_docs_and_contract_are_served_under_api(client: TestClient, path: str) -> None:
    assert client.get(path).status_code == 200


@pytest.mark.parametrize(
    ("old", "new"),
    [("/docs", "/api/docs"), ("/redoc", "/api/redoc"), ("/openapi.json", "/api/openapi.json")],
)
def test_old_docs_urls_redirect_permanently(client: TestClient, old: str, new: str) -> None:
    response = client.get(old, follow_redirects=False)
    assert response.status_code == 308
    assert response.headers["location"] == new
