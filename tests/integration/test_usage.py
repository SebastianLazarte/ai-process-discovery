"""RS-114: daily usage counters that outlive the purge, read with a server command (ADR 0020)."""

from datetime import date, timedelta
from typing import Any
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import inspect, select, update
from sqlalchemy.exc import OperationalError

from app.core.config import Settings
from app.core.db import build_engine, session_factory
from app.models.persistence import ProcessORM, UsageCounterORM
from app.models.persistence.base import utcnow
from app.purge import main as purge
from app.repositories.usage_repository import UsageRepository
from app.services import usage_service
from app.services.usage_service import UsageEvent, UsageService
from app.usage import main as usage
from tests.payloads import process_payload, step_payload

DEMO = "zoning-quotes"


def _counts(database_url: str) -> dict[str, int]:
    """Today's counters by event name."""
    engine = build_engine(database_url)
    with session_factory(engine)() as session:
        rows = session.execute(
            select(UsageCounterORM.event, UsageCounterORM.count).where(
                UsageCounterORM.day == utcnow().date()
            )
        ).all()
    engine.dispose()
    return {event: count for event, count in rows}


def _created(response: Any) -> dict[str, Any]:
    assert response.status_code in {200, 201}, response.text
    body: dict[str, Any] = response.json()
    return body


def _process(client: TestClient, **overrides: Any) -> dict[str, Any]:
    return _created(client.post("/api/processes", json=process_payload(**overrides)))


def _analysis(client: TestClient, process_id: str) -> dict[str, Any]:
    return _created(client.post(f"/api/processes/{process_id}/analyses", json={}))


@pytest.mark.req("RS-114", criterion=1)
def test_each_counted_request_adds_one_to_its_event_for_today(
    client: TestClient, database_url: str
) -> None:
    process = _process(client)
    analysis = _analysis(client, process["id"])
    _created(
        client.post(
            f"/api/analyses/{analysis['id']}/overrides",
            json={
                "step_id": analysis["step_assessments"][0]["step_id"],
                "method": "MANUAL",
                "human_control": "REQUIRED",
                "reason": "Counted by the usage test",
            },
        )
    )
    _created(client.get(f"/api/analyses/{analysis['id']}/blueprint"))
    for _ in range(2):
        markdown = client.get(f"/api/analyses/{analysis['id']}/blueprint.md")
        assert markdown.status_code == 200, markdown.text
    _created(client.post(f"/api/demo-processes/{DEMO}"))

    assert _counts(database_url) == {
        "process_created": 1,
        "analysis_run": 1,
        "override_created": 1,
        "blueprint_viewed": 1,
        "blueprint_downloaded": 2,
        "demo_loaded": 1,
    }


@pytest.mark.req("RS-114", criterion=1)
def test_reads_and_edits_are_not_counted(client: TestClient, database_url: str) -> None:
    process = _process(client)
    _created(client.get("/api/processes"))
    _created(client.get(f"/api/processes/{process['id']}"))
    _created(client.patch(f"/api/processes/{process['id']}", json={"name": "Edited"}))

    assert _counts(database_url) == {"process_created": 1}


@pytest.mark.req("RS-114", criterion=2)
def test_loading_a_demo_counts_only_the_demo(client: TestClient, database_url: str) -> None:
    process = _created(client.post(f"/api/demo-processes/{DEMO}"))
    assert client.get(f"/api/processes/{process['id']}/analyses").json(), "demo has no analysis"

    assert _counts(database_url) == {"demo_loaded": 1}


@pytest.mark.req("RS-114", criterion=3)
def test_failed_requests_change_no_counter(client: TestClient, database_url: str) -> None:
    missing = "00000000-0000-0000-0000-000000000000"
    sensitive = _process(client, steps=[step_payload(handles_sensitive_data=True)])
    before = _counts(database_url)

    assert client.post("/api/processes", json={"name": ""}).status_code == 422
    assert client.post("/api/demo-processes/no-such-demo").status_code == 404
    assert client.post(f"/api/processes/{missing}/analyses", json={}).status_code == 404
    assert (
        client.post(
            f"/api/processes/{sensitive['id']}/analyses", json={"use_llm": True}
        ).status_code
        == 409
    )
    assert client.get(f"/api/analyses/{missing}/blueprint").status_code == 404
    assert client.get(f"/api/analyses/{missing}/blueprint.md").status_code == 404

    assert _counts(database_url) == before == {"process_created": 1}


@pytest.mark.req("RS-114", criterion=4)
def test_purge_keeps_the_counters_and_they_hold_nothing_about_visitors(
    client: TestClient, database_url: str
) -> None:
    process = _process(client)
    _analysis(client, process["id"])
    engine = build_engine(database_url)
    with session_factory(engine)() as session:
        session.execute(
            update(ProcessORM)
            .where(ProcessORM.id == UUID(process["id"]))
            .values(created_at=utcnow() - timedelta(hours=25))
        )
        session.commit()
    columns = {column["name"] for column in inspect(engine).get_columns("usage_counters")}
    engine.dispose()

    assert purge(["--older-than-hours", "24"], Settings(database_url=database_url)) == 0

    assert client.get(f"/api/processes/{process['id']}").status_code == 404
    assert _counts(database_url) == {"process_created": 1, "analysis_run": 1}
    assert columns == {"day", "event", "count"}


@pytest.mark.req("RS-114", criterion=5)
def test_command_prints_one_row_per_day_newest_first_with_zeros_and_a_total(
    database_url: str, capsys: pytest.CaptureFixture[str]
) -> None:
    today = utcnow().date()
    engine = build_engine(database_url)
    UsageCounterORM.metadata.create_all(engine)
    with session_factory(engine)() as session:
        repo = UsageRepository(session)
        for day, event, times in [
            (today, "demo_loaded", 2),
            (today, "process_created", 1),
            (today - timedelta(days=2), "analysis_run", 3),
            (today - timedelta(days=9), "demo_loaded", 5),  # outside the window
        ]:
            for _ in range(times):
                repo.increment(day, event)
        session.commit()
    engine.dispose()

    assert usage(["--days", "7"], Settings(database_url=database_url)) == 0

    lines = capsys.readouterr().out.splitlines()
    assert lines[0].split() == ["day", *(event.value for event in UsageEvent)]
    days = [line.split()[0] for line in lines[1:-1]]
    assert days == [(today - timedelta(days=n)).isoformat() for n in range(7)]
    assert lines[1].split()[1:] == ["2", "1", "0", "0", "0", "0"]
    assert lines[3].split()[1:] == ["0", "0", "3", "0", "0", "0"]
    assert lines[2].split()[1:] == ["0"] * 6
    assert lines[-1].split() == ["total", "2", "1", "3", "0", "0", "0"]


@pytest.mark.req("RS-114", criterion=5)
@pytest.mark.parametrize("days", ["0", "-1", "a week"])
def test_command_rejects_a_window_that_is_not_a_positive_number_of_days(days: str) -> None:
    with pytest.raises(SystemExit):
        usage(["--days", days], Settings(database_url="sqlite://"))


@pytest.mark.req("RS-114", criterion=5)
def test_report_without_counters_lists_zeros(database_url: str) -> None:
    engine = build_engine(database_url)
    UsageCounterORM.metadata.create_all(engine)
    with session_factory(engine)() as session:
        report = UsageService(session).report(2, today=date(2026, 11, 7))
    engine.dispose()

    assert [entry.day for entry in report] == [date(2026, 11, 7), date(2026, 11, 6)]
    assert all(count == 0 for entry in report for count in entry.counts.values())


@pytest.mark.req("RS-114", criterion=6)
def test_a_counter_that_cannot_be_written_never_fails_the_request(
    client: TestClient, database_url: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    def broken(self: UsageRepository, day: date, event: str) -> None:
        raise OperationalError("INSERT INTO usage_counters", {}, Exception("disk full"))

    warnings: list[tuple[str, dict[str, Any]]] = []
    monkeypatch.setattr(UsageRepository, "increment", broken)
    monkeypatch.setattr(
        usage_service.logger,
        "warning",
        lambda message, extra: warnings.append((message, extra)),
    )

    process = _process(client)

    assert client.get(f"/api/processes/{process['id']}").status_code == 200
    assert warnings == [("usage_not_recorded", {"event": "process_created"})]
    assert _counts(database_url) == {}
