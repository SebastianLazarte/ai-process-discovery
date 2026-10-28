"""The deploy job of the release workflow and its two scripts (RS-67).

The scripts run against fake ssh and curl commands that record what they were asked to do.
The workflow is checked as text, job by job, like the other workflow tests in this suite.
"""

import os
import re
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = (ROOT / ".github" / "workflows" / "release.yml").read_text(encoding="utf-8")
RELEASE_DEPLOY = ROOT / "deploy" / "release-deploy.sh"
SMOKE_TEST = ROOT / "deploy" / "smoke-test.sh"
BASH = shutil.which("bash")
KNOWN_HOSTS = "demo-host ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIPinnedHostKeyForTheTestOnly"

pytestmark = pytest.mark.skipif(BASH is None, reason="the deploy scripts need bash")

FAKE_SSH = """#!/usr/bin/env bash
printf '%s\\n' "$@" >"$FAKE_STATE/ssh_args"
for arg in "$@"; do
  case "$arg" in
    UserKnownHostsFile=*) cp "${arg#*=}" "$FAKE_STATE/known_hosts" ;;
  esac
done
"""

FAKE_CURL = """#!/usr/bin/env bash
url="${*: -1}"
echo "$* " >>"$FAKE_STATE/curl_calls"
[[ -z "${FAKE_FAIL_PATH:-}" || "$url" != *"$FAKE_FAIL_PATH" ]]
"""


def _jobs(workflow: str) -> dict[str, str]:
    """Split the `jobs:` section into one text block per job."""
    section = workflow.split("\njobs:\n", 1)[1]
    names = list(re.finditer(r"^  ([a-z-]+):\n", section, flags=re.MULTILINE))
    return {
        match.group(1): section[match.end() : nxt.start() if nxt else len(section)]
        for match, nxt in zip(names, [*names[1:], None], strict=True)
    }


JOBS = _jobs(WORKFLOW)


class Runner:
    def __init__(self, root: Path) -> None:
        self.state = root / "state"
        self.bin = root / "bin"
        for folder in (self.state, self.bin):
            folder.mkdir()
        for name, body in (("ssh", FAKE_SSH), ("curl", FAKE_CURL)):
            fake = self.bin / name
            fake.write_bytes(body.encode())
            fake.chmod(0o755)

    def run(self, script: Path, *args: str, **env: str) -> subprocess.CompletedProcess[str]:
        assert BASH is not None
        variables = {
            key: value
            for key, value in os.environ.items()
            if not key.startswith(("DEPLOY_", "FAKE_"))
        }
        variables.update(
            {
                "PATH": f"{self.bin}{os.pathsep}{os.environ['PATH']}",
                "FAKE_STATE": self.state.as_posix(),
                **env,
            }
        )
        return subprocess.run(
            [BASH, script.as_posix(), *args],
            env=variables,
            capture_output=True,
            text=True,
            check=False,
        )

    def read(self, name: str) -> list[str]:
        path = self.state / name
        return path.read_text().splitlines() if path.exists() else []


@pytest.fixture
def runner(tmp_path: Path) -> Runner:
    return Runner(tmp_path)


SECRETS = {
    "DEPLOY_HOST": "demo-host",
    "DEPLOY_SSH_KEY": "fake deploy key\nsecond line",
    "DEPLOY_KNOWN_HOSTS": KNOWN_HOSTS,
}


# Criterion 1: the deploy job runs only in the production environment, over SSH with the
# pinned host key.


@pytest.mark.req("RS-67", criterion=1)
def test_the_deploy_job_runs_only_in_the_production_environment() -> None:
    deploy = JOBS["deploy"]
    assert re.search(r"environment:\n\s+name: production\n", deploy)
    assert "needs: [release-please, publish-image]" in deploy
    assert "needs.publish-image.result == 'success'" in deploy
    assert "vars.DEPLOY_ENABLED == 'true'" in deploy
    for name, job in JOBS.items():
        if name != "deploy":
            assert "environment:" not in job, name
            assert "secrets.DEPLOY_" not in job, name
    assert len(re.findall(r"secrets\.DEPLOY_", WORKFLOW)) == 3


@pytest.mark.req("RS-67", criterion=1)
def test_the_tag_reaches_the_scripts_through_the_environment_only() -> None:
    deploy = JOBS["deploy"]
    runs = re.findall(r"run: (.+)", deploy)
    assert runs == ['deploy/release-deploy.sh "$TAG"', 'deploy/smoke-test.sh "$DEMO_URL"']
    assert "${{" not in "".join(runs)


@pytest.mark.req("RS-67", criterion=1)
def test_ssh_checks_the_pinned_host_key_and_sends_only_the_tag(runner: Runner) -> None:
    result = runner.run(RELEASE_DEPLOY, "v1.4.0", **SECRETS)

    assert result.returncode == 0, result.stderr
    args = runner.read("ssh_args")
    assert "StrictHostKeyChecking=yes" in args
    assert "BatchMode=yes" in args
    assert "GlobalKnownHostsFile=/dev/null" in args
    assert any(arg.startswith("UserKnownHostsFile=") for arg in args)
    assert runner.read("known_hosts") == [KNOWN_HOSTS]
    assert args[-2:] == ["apd@demo-host", "v1.4.0"]


@pytest.mark.req("RS-67", criterion=1)
@pytest.mark.parametrize("missing", ["DEPLOY_HOST", "DEPLOY_SSH_KEY", "DEPLOY_KNOWN_HOSTS"])
def test_a_missing_secret_stops_before_ssh(runner: Runner, missing: str) -> None:
    result = runner.run(RELEASE_DEPLOY, "v1.4.0", **{**SECRETS, missing: ""})

    assert result.returncode != 0
    assert f"{missing} is empty" in result.stderr
    assert runner.read("ssh_args") == []


@pytest.mark.req("RS-67", criterion=1)
@pytest.mark.parametrize("tag", ["1.4.0", "v1.4", "latest", "v1.4.0; reboot"])
def test_a_tag_outside_vxyz_stops_before_ssh(runner: Runner, tag: str) -> None:
    result = runner.run(RELEASE_DEPLOY, tag, **SECRETS)

    assert result.returncode != 0
    assert runner.read("ssh_args") == []


# Criterion 2: after the deploy, the smoke test checks the site over HTTPS and fails the job
# on any error. RS-79 moved the paths to / and /api/health (ADR 0016).


@pytest.mark.req("RS-67", criterion=2)
def test_the_smoke_test_runs_after_the_deploy_in_the_same_job() -> None:
    deploy = JOBS["deploy"]
    assert deploy.index("name: Deploy over SSH") < deploy.index("name: Smoke test over HTTPS")


@pytest.mark.req("RS-67", criterion=2)
@pytest.mark.req("RS-79", criterion=3)
def test_the_smoke_test_checks_the_home_page_and_the_api_over_https(runner: Runner) -> None:
    result = runner.run(SMOKE_TEST, "https://apd.example.com/")

    assert result.returncode == 0, result.stderr
    calls = runner.read("curl_calls")
    assert [call.split()[-1] for call in calls] == [
        "https://apd.example.com/",
        "https://apd.example.com/api/health",
    ]
    for call in calls:
        assert "--fail" in call.split()
        assert "--proto =https" in call


@pytest.mark.req("RS-67", criterion=2)
@pytest.mark.req("RS-79", criterion=3)
@pytest.mark.parametrize("failing", ["/", "/api/health"])
def test_the_smoke_test_fails_when_a_path_fails(runner: Runner, failing: str) -> None:
    result = runner.run(SMOKE_TEST, "https://apd.example.com", FAKE_FAIL_PATH=failing)

    assert result.returncode != 0
    assert f"https://apd.example.com{failing} failed over HTTPS" in result.stderr


@pytest.mark.req("RS-67", criterion=2)
def test_the_smoke_test_refuses_plain_http(runner: Runner) -> None:
    result = runner.run(SMOKE_TEST, "http://apd.example.com")

    assert result.returncode != 0
    assert runner.read("curl_calls") == []


@pytest.mark.req("RS-67")
@pytest.mark.skipif(shutil.which("shellcheck") is None, reason="shellcheck runs in CI")
@pytest.mark.parametrize("script", [RELEASE_DEPLOY, SMOKE_TEST], ids=lambda p: p.name)
def test_shellcheck_passes(script: Path) -> None:
    subprocess.run(["shellcheck", script.as_posix()], check=True)
