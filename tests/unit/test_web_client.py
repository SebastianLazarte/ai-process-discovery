"""Static checks on the web client (RS-47, RS-49, RS-50).

The client is plain JavaScript, so its contract with the API is checked here, in the
same suite that owns the API: every endpoint the client calls must exist in OpenAPI.
"""

import re
from pathlib import Path

import pytest

from app.api.routes.web import WEB_FILES
from app.core.config import Settings
from app.main import create_app

ROOT = Path(__file__).resolve().parents[2]
WEB = ROOT / "web"
ENDPOINT = re.compile(r"\[\s*'(GET|POST|PUT|PATCH|DELETE)'\s*,\s*'([^']+)'\s*\]")


def _sources() -> dict[str, str]:
    return {path.name: path.read_text(encoding="utf-8") for path in WEB.glob("*.js")}


def _client_endpoints() -> list[tuple[str, str]]:
    return ENDPOINT.findall((WEB / "api.js").read_text(encoding="utf-8"))


def test_client_declares_endpoints() -> None:
    assert len(_client_endpoints()) >= 15


@pytest.mark.parametrize(("method", "path"), _client_endpoints())
def test_every_client_endpoint_exists_in_the_api(method: str, path: str) -> None:
    schema = create_app(Settings(database_url="sqlite://", log_level="WARNING")).openapi()
    assert path in schema["paths"], path
    assert method.lower() in schema["paths"][path], f"{method} {path}"


def test_only_api_js_calls_fetch() -> None:
    offenders = [name for name, text in _sources().items() if "fetch(" in text and name != "api.js"]
    assert offenders == []


def test_only_format_js_turns_strings_into_numbers() -> None:
    pattern = re.compile(r"\b(parseFloat|parseInt|Number)\(")
    offenders = [
        name for name, text in _sources().items() if pattern.search(text) and name != "format.js"
    ]
    assert offenders == []


def test_served_files_match_the_client_folder() -> None:
    on_disk = {path.name for path in WEB.iterdir() if path.is_file()}
    served = {name or "index.html" for name in WEB_FILES}
    assert served == on_disk


def test_index_has_no_inline_script_or_style() -> None:
    index = (WEB / "index.html").read_text(encoding="utf-8")
    assert re.search(r"<script(?![^>]*\bsrc=)[^>]*>", index) is None
    assert "<style" not in index
    assert "style=" not in index


def test_views_emit_no_inline_styles() -> None:
    offenders = [name for name, text in _sources().items() if "style=" in text]
    assert offenders == []
