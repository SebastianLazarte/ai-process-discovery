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


def _zones(config: str) -> dict[str, tuple[str, str]]:
    found = re.findall(r"^limit_req_zone\s+(\S+)\s+zone=(\w+):\S+\s+rate=(\S+);", config, re.M)
    return {zone: (key, rate) for key, zone, rate in found}


def _analysis_key(config: str) -> str:
    [key] = re.findall(r"map \$request_method \$apd_analysis_key \{\s*POST\s+(\S+);", config)
    return key


@pytest.mark.req("RS-65")
def test_production_limits_each_client_address() -> None:
    # The host site keys both zones on the address alone: no request header picks a bucket.
    assert _zones(SITE) == {
        "apd_analyses": ("$apd_analysis_key", "10r/m"),
        "apd_general": ("$binary_remote_addr", "10r/s"),
    }
    assert _analysis_key(SITE) == "$binary_remote_addr"


@pytest.mark.req("RS-78")
@pytest.mark.req("RS-65")
def test_the_edge_has_the_production_rates_with_one_bucket_per_test() -> None:
    # The end-to-end tests run one after another from one address, each in a fresh browser
    # context. The edge adds their X-E2E-Visitor header to the key, so a test never starts
    # with the burst the previous one spent; the rates and bursts stay those of production.
    site, edge = _zones(SITE), _zones(EDGE)
    assert {zone: rate for zone, (_, rate) in edge.items()} == {
        zone: rate for zone, (_, rate) in site.items()
    }
    assert edge["apd_general"][0] == "$binary_remote_addr$http_x_e2e_visitor"
    assert edge["apd_analyses"][0] == "$apd_analysis_key"
    assert _analysis_key(EDGE) == "$binary_remote_addr$http_x_e2e_visitor"
    # The header stops at the edge: the api and web containers never receive it.
    assert re.search(r'^\s*proxy_set_header X-E2E-Visitor "";', EDGE, flags=re.MULTILINE)
