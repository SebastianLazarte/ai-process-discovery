"""Web client served by the API (RS-46, RS-47, RS-48)."""

from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.api.routes.web import CONTENT_SECURITY_POLICY
from app.core.config import DEFAULT_WEB_DIR, Settings
from app.llm.providers.fake import FakeLLMProvider
from app.main import create_app


def _client(database_url: str, web_dir: Path) -> TestClient:
    settings = Settings(database_url=database_url, log_level="WARNING", web_dir=web_dir)
    return TestClient(create_app(settings, FakeLLMProvider()), follow_redirects=False)


@pytest.fixture
def web(database_url: str) -> Iterator[TestClient]:
    with _client(database_url, DEFAULT_WEB_DIR) as client:
        yield client


def test_root_redirects_to_the_client(web: TestClient) -> None:
    response = web.get("/")
    assert response.status_code == 307
    assert response.headers["location"] == "/ui/"
    assert web.get("/ui").headers["location"] == "/ui/"


def test_index_and_modules_are_served(web: TestClient) -> None:
    index = web.get("/ui/")
    assert index.status_code == 200
    assert index.headers["content-type"].startswith("text/html")
    assert 'src="app.js"' in index.text
    script = web.get("/ui/app.js")
    assert script.status_code == 200
    assert script.headers["content-type"].startswith("text/javascript")


@pytest.mark.parametrize(
    "path",
    [
        "/ui/tests/views.test.js",
        "/ui/tests/fixtures.js",
        "/ui/../pyproject.toml",
        "/ui/index.html",
        "/ui/CLAUDE.md",
    ],
)
def test_only_listed_files_are_served(web: TestClient, path: str) -> None:
    assert web.get(path).status_code == 404


def test_client_responses_carry_security_headers(web: TestClient) -> None:
    for path in ("/ui/", "/ui/styles.css", "/ui/missing.js"):
        headers = web.get(path).headers
        assert headers["content-security-policy"] == CONTENT_SECURITY_POLICY
        assert headers["x-content-type-options"] == "nosniff"
        assert headers["referrer-policy"] == "no-referrer"


def test_api_docs_keep_their_own_headers(web: TestClient) -> None:
    response = web.get("/api/docs")
    assert response.status_code == 200
    assert "content-security-policy" not in response.headers


def test_api_runs_without_the_client(database_url: str, tmp_path: Path) -> None:
    with _client(database_url, tmp_path / "missing") as client:
        assert client.get("/health").status_code == 200
        assert client.get("/ui/").status_code == 404
        assert client.get("/").status_code == 404
