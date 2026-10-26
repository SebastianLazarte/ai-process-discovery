"""RS-63: the purge command deletes expired demo data, and no HTTP route can trigger it."""

import re
from collections.abc import Callable
from datetime import timedelta
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select, update

from app.core.config import Settings
from app.core.db import build_engine, session_factory
from app.models.persistence import AnalysisORM, OverrideORM, ProcessORM, ProcessStepORM
from app.models.persistence.base import utcnow
from app.purge import main as purge
from app.services.retention_service import RetentionService
from tests.payloads import process_payload


def _process(client: TestClient) -> dict:  # type: ignore[type-arg]
    response = client.post("/api/processes", json=process_payload())
    assert response.status_code == 201, response.text
    return response.json()


def _analyse(client: TestClient, process_id: str) -> dict:  # type: ignore[type-arg]
    response = client.post(f"/api/processes/{process_id}/analyses", json={})
    assert response.status_code == 201, response.text
    return response.json()


def _override(client: TestClient, analysis: dict) -> None:  # type: ignore[type-arg]
    response = client.post(
        f"/api/analyses/{analysis['id']}/overrides",
        json={
            "step_id": analysis["step_assessments"][0]["step_id"],
            "method": "MANUAL",
            "human_control": "REQUIRED",
            "reason": "Kept manual for the purge test",
        },
    )
    assert response.status_code == 201, response.text


def _age(database_url: str, process_id: str, hours: int) -> None:
    """Move a process's creation time into the past, as if it had been stored earlier."""
    engine = build_engine(database_url)
    with session_factory(engine)() as session:
        session.execute(
            update(ProcessORM)
            .where(ProcessORM.id == UUID(process_id))
            .values(created_at=utcnow() - timedelta(hours=hours))
        )
        session.commit()
    engine.dispose()


def _count(database_url: str, column: object, process_id: str) -> int:
    engine = build_engine(database_url)
    with session_factory(engine)() as session:
        if column is OverrideORM:
            statement = (
                select(func.count())
                .select_from(OverrideORM)
                .join(AnalysisORM)
                .where(AnalysisORM.process_id == UUID(process_id))
            )
        else:
            statement = (
                select(func.count())
                .select_from(column)  # type: ignore[arg-type]
                .where(column.process_id == UUID(process_id))  # type: ignore[attr-defined]
            )
        count = session.scalar(statement) or 0
    engine.dispose()
    return count


@pytest.mark.req("RS-63", criterion=1)
def test_purge_deletes_only_expired_processes_with_their_analyses_and_overrides(
    client: TestClient, database_url: str
) -> None:
    old = _process(client)
    old_analysis = _analyse(client, old["id"])
    _override(client, old_analysis)
    new = _process(client)
    new_analysis = _analyse(client, new["id"])
    _age(database_url, old["id"], hours=25)

    assert purge(["--older-than-hours", "24"], Settings(database_url=database_url)) == 0

    assert client.get(f"/api/processes/{old['id']}").status_code == 404
    assert client.get(f"/api/analyses/{old_analysis['id']}").status_code == 404
    for owned in (ProcessStepORM, AnalysisORM, OverrideORM):
        assert _count(database_url, owned, old["id"]) == 0, owned.__name__
    assert client.get(f"/api/processes/{new['id']}").status_code == 200
    assert client.get(f"/api/analyses/{new_analysis['id']}").status_code == 200


@pytest.mark.req("RS-63", criterion=1)
def test_purge_counts_age_from_creation_not_from_the_last_edit(
    client: TestClient, database_url: str
) -> None:
    process = _process(client)
    _age(database_url, process["id"], hours=25)
    edited = client.patch(f"/api/processes/{process['id']}", json={"name": "Edited today"})
    assert edited.status_code == 200, edited.text

    purge(["--older-than-hours", "24"], Settings(database_url=database_url))

    assert client.get(f"/api/processes/{process['id']}").status_code == 404


@pytest.mark.req("RS-63")
@pytest.mark.parametrize("hours", ["0", "-3", "a day"])
def test_purge_rejects_a_window_that_is_not_a_positive_number_of_hours(hours: str) -> None:
    with pytest.raises(SystemExit):
        purge(["--older-than-hours", hours], Settings(database_url="sqlite://"))


@pytest.mark.req("RS-63", criterion=2)
def test_no_http_route_triggers_a_purge(
    make_client: Callable[..., TestClient],
    fake_provider: object,
    database_url: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[timedelta] = []
    monkeypatch.setattr(
        RetentionService, "purge", lambda self, retention, now=None: calls.append(retention)
    )
    client = make_client(fake_provider)
    # Never named in a request: it disappears only if something purges.
    untouched = _process(client)
    _age(database_url, untouched["id"], hours=72)
    target = _process(client)
    analysis = _analyse(client, target["id"])
    values = {
        "process_id": target["id"],
        "analysis_id": analysis["id"],
        "step_id": target["steps"][0]["id"],
        "slug": "no-such-demo",
        "name": "index.html",
    }

    # Every documented operation under /api, plus the routes kept out of the schema on purpose.
    operations = [
        (method.upper(), f"/api{path}")
        for path, item in client.get("/api/openapi.json").json()["paths"].items()
        for method in item
    ]
    operations += [
        ("GET", path) for path in ("/docs", "/redoc", "/openapi.json", "/api/docs", "/api/redoc")
    ]
    for method, template in operations:
        path = re.sub(r"\{(\w+)\}", lambda m: values[m.group(1)], template)
        client.request(method, path, json=None if method == "GET" else {})

    assert len(operations) >= 20, operations
    assert calls == []
    assert client.get(f"/api/processes/{untouched['id']}").status_code == 200
