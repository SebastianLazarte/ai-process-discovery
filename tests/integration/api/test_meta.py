"""Deployment metadata for the client (RS-62)."""

from fastapi.testclient import TestClient

from app import __version__
from app.core.config import Settings
from app.llm.providers.fake import FakeLLMProvider
from app.main import create_app


def _meta(database_url: str, **overrides: object) -> dict[str, object]:
    settings = Settings(database_url=database_url, log_level="WARNING", **overrides)  # type: ignore[arg-type]
    with TestClient(create_app(settings, FakeLLMProvider())) as client:
        response = client.get("/meta")
    assert response.status_code == 200
    body: dict[str, object] = response.json()
    return body


def test_meta_reports_version_and_a_private_deployment_by_default(database_url: str) -> None:
    assert _meta(database_url) == {"version": __version__, "public_demo": False}


def test_meta_reports_a_public_demo(database_url: str) -> None:
    assert _meta(database_url, public_demo=True)["public_demo"] is True
