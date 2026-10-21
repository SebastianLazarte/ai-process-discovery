"""RS-69, RS-80: the API answers under /api only; the root belongs to Next.js (ADR 0016)."""

import re

import pytest
from fastapi.testclient import TestClient

MISSING = "00000000-0000-4000-8000-000000000000"


def _operations(client: TestClient) -> list[tuple[str, str]]:
    paths = client.get("/api/openapi.json").json()["paths"]
    return [(method.upper(), path) for path, item in paths.items() for method in item]


def test_processes_answer_under_api_and_not_at_the_root(client: TestClient) -> None:
    assert client.get("/api/processes").status_code == 200
    assert client.get("/processes").status_code == 404


def test_no_documented_operation_answers_at_the_root(client: TestClient) -> None:
    # Unknown ids and empty bodies, so each call fails the same safe way and changes nothing.
    operations = _operations(client)
    assert len(operations) >= 15, operations
    for method, template in operations:
        path = re.sub(r"\{\w+\}", MISSING, template)
        body = None if method in ("GET", "DELETE") else {}
        assert client.request(method, path, json=body).status_code in (404, 405), (method, path)


def test_health_answers_only_under_api(client: TestClient) -> None:
    assert client.get("/api/health").status_code == 200
    assert client.get("/health").status_code == 404


@pytest.mark.parametrize("path", ["/", "/ui", "/ui/", "/ui/app.js"])
def test_the_api_no_longer_serves_a_client(client: TestClient, path: str) -> None:
    assert client.get(path, follow_redirects=False).status_code == 404


@pytest.mark.parametrize("path", ["/api/docs", "/api/redoc", "/api/openapi.json"])
def test_docs_and_contract_are_served_under_api(client: TestClient, path: str) -> None:
    assert client.get(path).status_code == 200


@pytest.mark.parametrize(
    ("old", "new"),
    [("/docs", "/api/docs"), ("/redoc", "/api/redoc"), ("/openapi.json", "/api/openapi.json")],
)
def test_old_docs_urls_redirect_permanently(client: TestClient, old: str, new: str) -> None:
    response = client.get(old, follow_redirects=False)
    assert response.status_code == 301
    assert response.headers["location"] == new


def test_api_docs_keep_their_own_headers(client: TestClient) -> None:
    response = client.get("/api/docs")
    assert response.status_code == 200
    assert "content-security-policy" not in response.headers
