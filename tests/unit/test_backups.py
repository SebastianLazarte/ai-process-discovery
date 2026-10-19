"""Nightly backup and purge, the restore rehearsal and the data policy (RS-68).

The scripts run against a fake docker command that records its calls. The systemd units,
the runbook, the README and SECURITY.md are checked as text. The purge command itself is
covered by tests/integration/test_purge.py (RS-63).
"""

import configparser
import os
import re
import shutil
import subprocess
import time
from datetime import UTC, datetime
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
BACKUP = ROOT / "deploy" / "backup.sh"
REHEARSAL = ROOT / "deploy" / "restore-rehearsal.sh"
UNITS = ROOT / "deploy" / "systemd"
RUNBOOK = (ROOT / "docs" / "runbook" / "production.md").read_text(encoding="utf-8")
BASH = shutil.which("bash")
DAY = 24 * 60 * 60

FAKE_DOCKER = """#!/usr/bin/env bash
echo "docker $*" >>"$FAKE_STATE/calls"
case "$*" in
  *"pg_dump"*) [[ -z "${FAKE_FAIL_DUMP:-}" ]] && echo "nightly dump" ;;
  "compose config --images") echo "postgres:17.11@sha256:abc"; echo "ghcr.io/x/api:1.4.0" ;;
  *"pg_restore"*) cat >"$FAKE_STATE/restored" ;;
  *"SELECT count(*) FROM processes"*) echo 3 ;;
  *"SELECT count(*) FROM process_steps"*) echo 19 ;;
  *"SELECT count(*) FROM analyses"*) echo 4 ;;
  *"SELECT count(*) FROM recommendation_overrides"*) echo 1 ;;
esac
"""


def _unit(name: str) -> configparser.ConfigParser:
    parser = configparser.ConfigParser(interpolation=None)
    parser.optionxform = str  # type: ignore[assignment,method-assign]
    parser.read(UNITS / name, encoding="utf-8")
    return parser


class Host:
    def __init__(self, root: Path) -> None:
        self.apd = root / "opt-apd"
        self.backups = root / "backups"
        self.state = root / "state"
        self.bin = root / "bin"
        for folder in (self.apd, self.backups, self.state, self.bin):
            folder.mkdir()
        fake = self.bin / "docker"
        fake.write_bytes(FAKE_DOCKER.encode())
        fake.chmod(0o755)

    def dump(self, name: str, age_days: float, content: str = "old dump") -> Path:
        path = self.backups / name
        path.write_text(content)
        moment = time.time() - age_days * DAY
        os.utime(path, (moment, moment))
        return path

    def run(self, script: Path, *args: str, **env: str) -> subprocess.CompletedProcess[str]:
        assert BASH is not None
        variables = {
            **{k: v for k, v in os.environ.items() if not k.startswith("FAKE_")},
            "PATH": f"{self.bin}{os.pathsep}{os.environ['PATH']}",
            "APD_DIR": self.apd.as_posix(),
            "BACKUP_DIR": self.backups.as_posix(),
            "FAKE_STATE": self.state.as_posix(),
            "READY_DELAY": "0",
            **env,
        }
        return subprocess.run(
            [BASH, script.as_posix(), *args],
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
    def names(self) -> set[str]:
        return {path.name for path in self.backups.iterdir()}


@pytest.fixture
def host(tmp_path: Path) -> Host:
    return Host(tmp_path)


needs_bash = pytest.mark.skipif(BASH is None, reason="the scripts need bash")


# Criterion 1: last night's backup, restored into a scratch database, is recorded in the
# runbook with its date.


@needs_bash
def test_the_rehearsal_restores_the_newest_dump_and_prints_a_runbook_row(host: Host) -> None:
    host.dump("nightly-20261017T003000Z.dump", 2, "older")
    host.dump("nightly-20261018T003000Z.dump", 1, "newest")
    host.dump("pre-deploy-20261018T120000Z-v1.3.1-to-v1.4.0.dump", 0.5, "deploy")

    result = host.run(REHEARSAL)

    assert result.returncode == 0, result.stderr
    assert (host.state / "restored").read_text() == "newest"
    today = datetime.now(UTC).strftime("%Y-%m-%d")
    assert result.stdout.splitlines()[-1] == (
        f"| {today} | nightly-20261018T003000Z.dump | Restored: processes 3, "
        "process_steps 19, analyses 4, recommendation_overrides 1 |"
    )


@needs_bash
def test_the_rehearsal_never_touches_the_live_database(host: Host) -> None:
    host.dump("nightly-20261018T003000Z.dump", 1)

    host.run(REHEARSAL)

    [run] = [call for call in host.calls if call.startswith("docker run ")]
    assert "--network none" in run
    assert "--volume" not in run and " -v " not in run
    assert "postgres:17.11@sha256:abc" in run
    assert not any("compose exec" in call or "compose run" in call for call in host.calls)
    assert host.calls[-1] == "docker rm --force apd-restore-rehearsal"


@needs_bash
def test_the_rehearsal_fails_without_a_dump(host: Host) -> None:
    result = host.run(REHEARSAL)

    assert result.returncode != 0
    assert "no nightly dump" in result.stderr
    assert host.calls == []


def test_the_runbook_has_a_dated_table_for_rehearsals() -> None:
    section = RUNBOOK.split("## Backups and restore", 1)[1].split("\n## ", 1)[0]
    assert "/opt/apd/restore-rehearsal.sh" in section
    assert "| Date | Dump | Result |" in section
    rows = [line for line in section.splitlines() if line.startswith("| ") and "---" not in line]
    for row in rows[1:]:
        first = row.split("|")[1].strip()
        assert not first or re.fullmatch(r"\d{4}-\d{2}-\d{2}", first), row


# Criterion 2: after a night with the timers, a new backup exists, backups older than 7 days
# are gone and expired processes are purged.


def test_the_purge_runs_before_the_backup_every_night() -> None:
    purge = _unit("apd-purge.timer")["Timer"]
    backup = _unit("apd-backup.timer")["Timer"]
    assert purge["OnCalendar"] == "*-*-* 00:05:00 UTC"
    assert backup["OnCalendar"] == "*-*-* 00:30:00 UTC"
    for timer in (purge, backup):
        assert timer["Persistent"] == "true"
    for name in ("apd-purge.timer", "apd-backup.timer"):
        assert _unit(name)["Install"]["WantedBy"] == "timers.target"


def test_the_services_run_as_apd_and_call_the_purge_and_the_backup() -> None:
    purge = _unit("apd-purge.service")["Service"]
    backup = _unit("apd-backup.service")["Service"]
    for service in (purge, backup):
        assert service["User"] == "apd"
        assert service["WorkingDirectory"] == "/opt/apd"
        assert service["Type"] == "oneshot"
    assert purge["ExecStart"] == (
        "/usr/bin/docker compose exec -T api python -m app.purge --older-than-hours 24"
    )
    assert backup["ExecStart"] == "/opt/apd/backup.sh"


@needs_bash
def test_a_night_writes_a_new_backup_and_deletes_those_older_than_7_days(host: Host) -> None:
    host.dump("nightly-old.dump", 8)
    host.dump("pre-deploy-old.dump", 7.5)
    host.dump("nightly-recent.dump", 6)
    host.dump("notes.txt", 30)

    result = host.run(BACKUP)

    assert result.returncode == 0, result.stderr
    [new] = [name for name in host.names if name.startswith("nightly-2")]
    assert (host.backups / new).read_text() == "nightly dump\n"
    assert host.names == {new, "nightly-recent.dump", "notes.txt"}
    assert host.calls == [
        "docker compose exec -T postgres pg_dump --username=apd --format=custom apd"
    ]


@needs_bash
def test_a_failed_dump_deletes_nothing(host: Host) -> None:
    host.dump("nightly-old.dump", 8)

    result = host.run(BACKUP, FAKE_FAIL_DUMP="1")

    assert result.returncode != 0
    assert host.names == {"nightly-old.dump"}


# Criterion 3: the README points to the live demo and SECURITY.md describes its data policy.


def test_the_readme_points_to_the_live_demo() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    try_it = readme.split("## Try it", 1)[1].split("\n## ", 1)[0]
    assert "**Live demo:**" in try_it
    assert "Website" in try_it
    assert "coming with" not in try_it


def test_security_describes_the_demo_data_policy() -> None:
    security = (ROOT / "SECURITY.md").read_text(encoding="utf-8")
    policy = security.split("## Public demo data", 1)[1].split("\n## ", 1)[0]
    for promise in ("24 hours", "7 days", "never leave the host", "synthetic"):
        assert promise in policy, promise


@pytest.mark.skipif(shutil.which("shellcheck") is None, reason="shellcheck runs in CI")
@pytest.mark.parametrize("script", [BACKUP, REHEARSAL], ids=lambda p: p.name)
def test_shellcheck_passes(script: Path) -> None:
    subprocess.run(["shellcheck", script.as_posix()], check=True)
