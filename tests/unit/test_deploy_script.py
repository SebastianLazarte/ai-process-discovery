"""deploy/deploy.sh against fake docker, curl and flock commands (RS-66).

The fakes log every docker call with the image version it ran under, remember which
version `up` started, and fail the health check for the version named in
FAKE_BROKEN_VERSION. The script runs in a temporary APD_DIR with its own .env.
"""

import os
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "deploy" / "deploy.sh"
BASH = shutil.which("bash")
PREVIOUS = "1.3.1"

pytestmark = pytest.mark.skipif(BASH is None, reason="deploy.sh needs bash")

FAKE_DOCKER = """#!/usr/bin/env bash
echo "APD_VERSION=$APD_VERSION docker $*" >>"$FAKE_STATE/calls"
case "$*" in
  *"pg_dump"*) echo "dump of $APD_VERSION" ;;
  *"alembic upgrade"*) [[ -z "${FAKE_FAIL_MIGRATION:-}" ]] ;;
  *" up "*) echo "$APD_VERSION" >"$FAKE_STATE/running" ;;
esac
"""

FAKE_CURL = """#!/usr/bin/env bash
[[ "$(cat "$FAKE_STATE/running")" != "${FAKE_BROKEN_VERSION:-}" ]]
"""

FAKE_FLOCK = "#!/usr/bin/env bash\nexit 0\n"


class Server:
    def __init__(self, root: Path) -> None:
        self.apd = root / "opt-apd"
        self.backups = root / "backups"
        self.state = root / "state"
        self.bin = root / "bin"
        for folder in (self.apd, self.state, self.bin):
            folder.mkdir()
        (self.apd / ".env").write_bytes(
            f"APD_VERSION={PREVIOUS}\nPOSTGRES_PASSWORD=secret\n".encode()
        )
        (self.state / "running").write_bytes(f"{PREVIOUS}\n".encode())
        for name, body in (("docker", FAKE_DOCKER), ("curl", FAKE_CURL), ("flock", FAKE_FLOCK)):
            fake = self.bin / name
            fake.write_bytes(body.encode())
            fake.chmod(0o755)

    def deploy(self, *args: str, **env: str) -> subprocess.CompletedProcess[str]:
        assert BASH is not None
        variables = {
            **os.environ,
            "PATH": f"{self.bin}{os.pathsep}{os.environ['PATH']}",
            "APD_DIR": self.apd.as_posix(),
            "BACKUP_DIR": self.backups.as_posix(),
            "FAKE_STATE": self.state.as_posix(),
            "HEALTH_ATTEMPTS": "2",
            "HEALTH_DELAY": "0",
            **env,
        }
        variables.pop("SSH_ORIGINAL_COMMAND", None)
        variables.update({k: v for k, v in env.items() if k == "SSH_ORIGINAL_COMMAND"})
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

    @property
    def env_version(self) -> str:
        return (self.apd / ".env").read_text().splitlines()[0].removeprefix("APD_VERSION=")

    @property
    def running(self) -> str:
        return (self.state / "running").read_text().strip()


@pytest.fixture
def server(tmp_path: Path) -> Server:
    return Server(tmp_path)


@pytest.mark.parametrize(
    "tag", ["1.4.0", "v1.4", "v1.4.0-rc.1", "latest", "v1.4.0; rm -rf /", "v1.4.0\nv1.5.0", ""]
)
def test_a_tag_outside_vxyz_changes_nothing(server: Server, tag: str) -> None:
    by_argument = server.deploy(tag) if tag else server.deploy()
    over_ssh = server.deploy(SSH_ORIGINAL_COMMAND=tag)

    for result in (by_argument, over_ssh):
        assert result.returncode != 0
        assert "expected a tag like v1.2.3" in result.stderr
    assert server.calls == []
    assert server.env_version == PREVIOUS
    assert server.running == PREVIOUS
    assert not server.backups.exists()


@pytest.mark.parametrize("over_ssh", [False, True], ids=["argument", "ssh"])
def test_a_valid_tag_backs_up_and_migrates_before_it_starts(server: Server, over_ssh: bool) -> None:
    result = server.deploy(SSH_ORIGINAL_COMMAND="v1.4.0") if over_ssh else server.deploy("v1.4.0")

    assert result.returncode == 0, result.stderr
    steps = [
        (f"APD_VERSION={PREVIOUS}", "pg_dump"),
        ("APD_VERSION=1.4.0", "pull api"),
        ("APD_VERSION=1.4.0", "run --rm api alembic upgrade head"),
        ("APD_VERSION=1.4.0", "up --detach api"),
    ]
    assert len(server.calls) == len(steps)
    for call, (version, action) in zip(server.calls, steps, strict=True):
        assert call.startswith(f"{version} docker compose"), call
        assert action in call, call
    [dump] = server.backups.iterdir()
    assert dump.name.endswith(f"-v{PREVIOUS}-to-v1.4.0.dump")
    assert dump.read_text() == f"dump of {PREVIOUS}\n"
    assert server.env_version == "1.4.0"
    assert server.running == "1.4.0"


def test_a_failing_health_check_starts_the_previous_version_again(server: Server) -> None:
    result = server.deploy("v1.4.0", FAKE_BROKEN_VERSION="1.4.0")

    assert result.returncode != 0
    assert f"rolled back to v{PREVIOUS}" in result.stderr
    assert server.calls[-2].startswith("APD_VERSION=1.4.0 docker compose up")
    assert server.calls[-1].startswith(f"APD_VERSION={PREVIOUS} docker compose up")
    assert server.running == PREVIOUS
    assert server.env_version == PREVIOUS
    assert len(list(server.backups.iterdir())) == 1


def test_a_failing_migration_never_starts_the_new_version(server: Server) -> None:
    result = server.deploy("v1.4.0", FAKE_FAIL_MIGRATION="1")

    assert result.returncode != 0
    assert not any(" up " in call for call in server.calls)
    assert server.running == PREVIOUS
    assert server.env_version == PREVIOUS


@pytest.mark.skipif(shutil.which("shellcheck") is None, reason="shellcheck runs in CI")
def test_shellcheck_passes() -> None:
    subprocess.run(["shellcheck", SCRIPT.as_posix()], check=True)
