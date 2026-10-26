"""The routes of the public demo from 2.0.0 (ADR 0016, RS-79).

deploy/nginx/apd-routes.conf is read into its locations, and a request path is matched the
way Nginx does it: the longest prefix location, unless a regex location matches first in
file order. The real Nginx runs the same file in the `docker` job of CI, through the edge
service of compose.yaml.
"""

import re
from dataclasses import dataclass
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
NGINX = ROOT / "deploy" / "nginx"
ROUTES = (NGINX / "apd-routes.conf").read_text(encoding="utf-8")
SITE = (NGINX / "apd.conf").read_text(encoding="utf-8")
EDGE = (NGINX / "edge.conf").read_text(encoding="utf-8")
SNIPPET = "include /etc/nginx/snippets/apd-routes.conf;"


@dataclass(frozen=True)
class Location:
    modifier: str
    pattern: str
    body: str

    def directive(self, name: str) -> list[str]:
        return re.findall(rf"^\s*{name}\s+([^;]+);", self.body, flags=re.MULTILINE)


def _locations(config: str) -> list[Location]:
    found = re.finditer(
        r"^location\s+(~\s+)?(\S+)\s*\{\n(.*?)^\}", config, re.MULTILINE | re.DOTALL
    )
    return [Location((m.group(1) or "").strip(), m.group(2), m.group(3)) for m in found]


LOCATIONS = _locations(ROUTES)


def route(path: str) -> Location:
    prefixes = [loc for loc in LOCATIONS if not loc.modifier and path.startswith(loc.pattern)]
    for location in LOCATIONS:
        if location.modifier == "~" and re.search(location.pattern, path):
            return location
    return max(prefixes, key=lambda loc: len(loc.pattern))


def upstream(path: str) -> str:
    location = route(path)
    [target] = location.directive("proxy_pass") or location.directive("return")
    return target


# Criterion 1: Next.js answers / and every path outside /api/; every path under /api/ goes to
# FastAPI.


@pytest.mark.req("RS-79", criterion=1)
@pytest.mark.parametrize(
    "path", ["/", "/processes/abc", "/processes/abc/results", "/_next/static/chunks/a.js", "/api"]
)
def test_paths_outside_api_go_to_nextjs(path: str) -> None:
    assert upstream(path) == "http://apd_web"


@pytest.mark.req("RS-79", criterion=1)
@pytest.mark.parametrize(
    "path", ["/api/health", "/api/meta", "/api/processes", "/api/processes/abc/steps", "/api/docs"]
)
def test_paths_under_api_go_to_fastapi(path: str) -> None:
    assert upstream(path) == "http://apd_api"


@pytest.mark.req("RS-80")
@pytest.mark.parametrize("path", ["/docs", "/redoc", "/openapi.json"])
def test_the_old_docs_urls_reach_fastapi_for_their_redirect(path: str) -> None:
    # FastAPI answers them with a 301 to /api/... (LEGACY_DOCS, RS-80). Without this route,
    # Next.js would answer 404.
    assert upstream(path) == "http://apd_api"


@pytest.mark.req("RS-79", criterion=1)
@pytest.mark.parametrize("path", ["/docs/x", "/redocs", "/openapi.json.bak", "/documents"])
def test_only_the_three_exact_doc_paths_leave_nextjs(path: str) -> None:
    assert upstream(path) == "http://apd_web"


@pytest.mark.req("RS-79", criterion=1)
@pytest.mark.req("RS-80", criterion=3)
@pytest.mark.parametrize("path", ["/ui", "/ui/", "/ui/index.html", "/ui/app.js"])
def test_the_retired_client_answers_301_to_the_home_page(path: str) -> None:
    assert upstream(path) == "301 /"


@pytest.mark.req("RS-79", criterion=1)
@pytest.mark.req("RS-64", criterion=2)
def test_the_host_and_the_edge_define_the_upstreams_and_include_the_same_routes() -> None:
    assert SNIPPET in SITE and SNIPPET in EDGE
    assert re.search(r"upstream apd_api \{\s*server 127\.0\.0\.1:8100;", SITE)
    assert re.search(r"upstream apd_web \{\s*server 127\.0\.0\.1:8101;", SITE)
    assert re.search(r"upstream apd_api \{\s*server api:8000;", EDGE)
    assert re.search(r"upstream apd_web \{\s*server web:3000;", EDGE)
    prod = (ROOT / "deploy" / "compose.prod.yaml").read_text(encoding="utf-8")
    assert '"127.0.0.1:8100:8000"' in prod and '"127.0.0.1:8101:3000"' in prod
    assert "${APD_WEB_VERSION:?" in prod
    compose = (ROOT / "compose.yaml").read_text(encoding="utf-8")
    assert "./deploy/nginx/apd-routes.conf:/etc/nginx/snippets/apd-routes.conf:ro" in compose


@pytest.mark.req("RS-79")
def test_no_route_sets_its_own_headers() -> None:
    # A location with add_header would drop the security headers of the host site.
    assert not re.search(r"^\s*add_header\s", ROUTES, flags=re.MULTILINE)


# Criterion 2: /api/processes/{id}/analyses gets the analysis rate limit and the long read
# timeout.


@pytest.mark.req("RS-79", criterion=2)
@pytest.mark.req("RS-65")
def test_analysis_runs_get_the_rate_limit_and_the_llm_timeout() -> None:
    location = route("/api/processes/3f2b/analyses")
    assert location.directive("proxy_pass") == ["http://apd_api"]
    assert "zone=apd_analyses burst=5 nodelay" in location.directive("limit_req")
    assert "zone=apd_general burst=40 nodelay" in location.directive("limit_req")
    [timeout] = location.directive("proxy_read_timeout")
    assert int(timeout.removesuffix("s")) >= 200


@pytest.mark.req("RS-79", criterion=2)
@pytest.mark.parametrize(
    "path", ["/api/processes/3f2b", "/api/processes/3f2b/analyses/9", "/processes/3f2b/analyses"]
)
def test_other_paths_do_not_get_the_analysis_limit(path: str) -> None:
    assert "zone=apd_analyses burst=5 nodelay" not in route(path).directive("limit_req")


@pytest.mark.req("RS-79", criterion=2)
@pytest.mark.req("RS-65")
def test_both_zones_exist_wherever_the_routes_are_included() -> None:
    for config in (SITE, EDGE):
        assert "zone=apd_general:10m" in config
        assert "zone=apd_analyses:10m" in config
