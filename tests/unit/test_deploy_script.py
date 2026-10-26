"""deploy/deploy.sh against fake docker, curl and flock commands (RS-66, RS-79).

The fakes log every docker call with the versions it ran under, remember which version
`up` started for each service, and fail the health check of a service whose running
version is named in FAKE_BROKEN_API or FAKE_BROKEN_WEB. The script runs in a temporary
APD_DIR with its own .env.
"""

import os
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "deploy" / "deploy.sh"
BASH = shutil.which("bash")
API = "1.6.0"
WEB = "1.6.0"

pytestmark = pytest.mark.skipif(BASH is None, reason="deploy.sh needs bash")

FAKE_DOCKER = """#!/usr/bin/env bash
echo "api=$APD_VERSION web=$APD_WEB_VERSION docker $*" >>"$FAKE_STATE/calls"
case "$*" in
  *"pg_dump"*) echo "dump of $APD_VERSION" ;;
  *"alembic upgrade"*) [[ -z "${FAKE_FAIL_MIGRATION:-}" ]] ;;
  *" up "*)
    [[ " $* " == *" api "* ]] && echo "$APD_VERSION" >"$FAKE_STATE/api"
    [[ " $* " == *" web "* ]] && echo "$APD_WEB_VERSION" >"$FAKE_STATE/web"
    true ;;
esac
"""

FAKE_CURL = """#!/usr/bin/env bash
url="${*: -1}"
if [[ "$url" == *":8101/"* ]]; then
  [[ "$(cat "$FAKE_STATE/web")" != "${FAKE_BROKEN_WEB:-}" ]]
else
  [[ "$(cat "$FAKE_STATE/api")" != "${FAKE_BROKEN_API:-}" ]]
fi
"""

FAKE_FLOCK = "#!/usr/bin/env bash\nexit 0\n"


class Server:
    def __init__(self, root: Path, api: str = API, web: str | None = WEB) -> None:
        self.apd = root / "opt-apd"
        self.backups = root / "backups"
        self.state = root / "state"
        self.bin = root / "bin"
        for folder in (self.apd, self.state, self.bin):
            folder.mkdir()
        lines = [f"APD_VERSION={api}", *([f"APD_WEB_VERSION={web}"] if web else [])]
        (self.apd / ".env").write_bytes(
            ("\n".join([*lines, "POSTGRES_PASSWORD=secret"]) + "\n").encode()
        )
        (self.state / "api").write_bytes(f"{api}\n".encode())
        (self.state / "web").write_bytes(f"{web}\n".encode())
        for name, body in (("docker", FAKE_DOCKER), ("curl", FAKE_CURL), ("flock", FAKE_FLOCK)):
            fake = self.bin / name
            fake.write_bytes(body.encode())
            fake.chmod(0o755)

    def deploy(self, *args: str, **env: str) -> subprocess.CompletedProcess[str]:
        assert BASH is not None
        variables = {
            **{k: v for k, v in os.environ.items() if not k.startswith("FAKE_")},
            "PATH": f"{self.bin}{os.pathsep}{os.environ['PATH']}",
            "APD_DIR": self.apd.as_posix(),
            "BACKUP_DIR": self.backups.as_posix(),
            "FAKE_STATE": self.state.as_posix(),
            "HEALTH_ATTEMPTS": "2",
            "HEALTH_DELAY": "0",
        }
        variables.pop("SSH_ORIGINAL_COMMAND", None)
        variables.update(env)
        return subprocess.run(
            [BASH, SCRIPT.as_posix(), *args],
            env=variables,
            capture_output=True,
            text=True,
            check=False,
        )

    @property
    def calls(self) -> list[str]:
        log = self.state / "calls"
        return log.read_text().splitlines() if log.exists() else []

    def env(self, name: str) -> str | None:
        for line in (self.apd / ".env").read_text().splitlines():
            if line.startswith(f"{name}="):
                return line.removeprefix(f"{name}=")
        return None

    def running(self, service: str) -> str:
        return (self.state / service).read_text().strip()


@pytest.fixture
def server(tmp_path: Path) -> Server:
    return Server(tmp_path)


# RS-66: one validated tag, a backup and the migrations before the start.


@pytest.mark.req("RS-66", criterion=1)
@pytest.mark.parametrize(
    "tag", ["1.7.0", "v1.7", "v1.7.0-rc.1", "latest", "v1.7.0; rm -rf /", "v1.7.0\nv1.8.0", ""]
)
def test_a_tag_outside_vxyz_changes_nothing(server: Server, tag: str) -> None:
    by_argument = server.deploy(tag) if tag else server.deploy()
    over_ssh = server.deploy(SSH_ORIGINAL_COMMAND=tag)

    for result in (by_argument, over_ssh):
        assert result.returncode != 0
        assert "expected a tag like v1.2.3" in result.stderr
    assert server.calls == []
    assert (server.env("APD_VERSION"), server.env("APD_WEB_VERSION")) == (API, WEB)
    assert not server.backups.exists()


@pytest.mark.req("RS-66", criterion=2)
@pytest.mark.parametrize("over_ssh", [False, True], ids=["argument", "ssh"])
def test_a_1x_tag_backs_up_migrates_and_moves_the_api_only(server: Server, over_ssh: bool) -> None:
    result = server.deploy(SSH_ORIGINAL_COMMAND="v1.7.0") if over_ssh else server.deploy("v1.7.0")

    assert result.returncode == 0, result.stderr
    assert server.calls == [
        f"api={API} web={WEB} docker compose exec -T postgres pg_dump --username=apd"
        " --format=custom apd",
        f"api=1.7.0 web={WEB} docker compose pull api",
        f"api=1.7.0 web={WEB} docker compose run --rm api alembic upgrade head",
        f"api=1.7.0 web={WEB} docker compose up --detach api",
    ]
    [dump] = server.backups.iterdir()
    assert dump.name.endswith(f"-v{API}-to-v1.7.0.dump")
    assert dump.read_text() == f"dump of {API}\n"
    assert (server.env("APD_VERSION"), server.env("APD_WEB_VERSION")) == ("1.7.0", WEB)
    assert (server.running("api"), server.running("web")) == ("1.7.0", WEB)


@pytest.mark.req("RS-66")
def test_a_failing_migration_never_starts_the_new_version(server: Server) -> None:
    result = server.deploy("v2.0.0", FAKE_FAIL_MIGRATION="1")

    assert result.returncode != 0
    assert not any(" up " in call for call in server.calls)
    assert (server.running("api"), server.running("web")) == (API, WEB)
    assert (server.env("APD_VERSION"), server.env("APD_WEB_VERSION")) == (API, WEB)


@pytest.mark.req("RS-79", criterion=4)
def test_a_missing_web_version_stops_before_any_docker_call(tmp_path: Path) -> None:
    server = Server(tmp_path, web=None)

    result = server.deploy("v1.7.0")

    assert result.returncode != 0
    assert "APD_WEB_VERSION is missing" in result.stderr
    assert server.calls == []


# RS-79: a 2.x tag moves both services, and a failed check puts each one back on the version
# that .env recorded for it.


@pytest.mark.req("RS-79", criterion=4)
def test_a_2x_tag_moves_both_services_and_checks_both(server: Server) -> None:
    result = server.deploy("v2.0.0")

    assert result.returncode == 0, result.stderr
    assert server.calls[1:] == [
        "api=2.0.0 web=2.0.0 docker compose pull api web",
        "api=2.0.0 web=2.0.0 docker compose run --rm api alembic upgrade head",
        "api=2.0.0 web=2.0.0 docker compose up --detach api web",
    ]
    assert (server.env("APD_VERSION"), server.env("APD_WEB_VERSION")) == ("2.0.0", "2.0.0")
    assert (server.running("api"), server.running("web")) == ("2.0.0", "2.0.0")


@pytest.mark.req("RS-79", criterion=4)
@pytest.mark.parametrize(
    ("api", "web", "broken"),
    [
        (API, WEB, "FAKE_BROKEN_API"),
        (API, WEB, "FAKE_BROKEN_WEB"),
        # S1 of ADR 0016: the API still on 1.x, the web already on 2.0.0.
        (API, "2.0.0", "FAKE_BROKEN_API"),
    ],
    ids=["api-fails", "web-fails", "from-s1"],
)
def test_a_failing_health_check_puts_each_service_back_on_its_version(
    tmp_path: Path, api: str, web: str, broken: str
) -> None:
    server = Server(tmp_path, api=api, web=web)

    result = server.deploy("v2.0.0", **{broken: "2.0.0"})

    assert result.returncode != 0
    assert f"rolled back to API v{api} and web v{web}" in result.stderr
    assert server.calls[-1] == f"api={api} web={web} docker compose up --detach api web"
    assert (server.running("api"), server.running("web")) == (api, web)
    assert (server.env("APD_VERSION"), server.env("APD_WEB_VERSION")) == (api, web)
    assert len(list(server.backups.iterdir())) == 1


@pytest.mark.req("RS-66", criterion=3)
def test_a_1x_tag_with_a_failing_api_check_restores_the_api_only(server: Server) -> None:
    result = server.deploy("v1.7.0", FAKE_BROKEN_API="1.7.0")

    assert result.returncode != 0
    assert server.calls[-1] == f"api={API} web={WEB} docker compose up --detach api"
    assert (server.running("api"), server.env("APD_VERSION")) == (API, API)


@pytest.mark.req("RS-66", criterion=4)
@pytest.mark.skipif(shutil.which("shellcheck") is None, reason="shellcheck runs in CI")
def test_shellcheck_passes() -> None:
    subprocess.run(["shellcheck", SCRIPT.as_posix()], check=True)
