from fastapi.testclient import TestClient

from tests.payloads import process_payload, step_payload


def _create(client: TestClient, **overrides: object) -> dict:  # type: ignore[type-arg]
    response = client.post("/processes", json=process_payload(**overrides))
    assert response.status_code == 201, response.text
    return response.json()


def test_health(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "ok"}


def test_create_and_read_process(client: TestClient) -> None:
    created = _create(client)
    assert created["version"] == 1
    assert created["hourly_cost"] == "18.50"
    assert created["steps"][0]["position"] == 1
    assert created["steps"][0]["minutes_per_execution"] == "4.0"

    fetched = client.get(f"/processes/{created['id']}").json()
    assert fetched == created

    listing = client.get("/processes").json()
    assert [(p["id"], p["step_count"]) for p in listing] == [(created["id"], 1)]


def test_update_process_bumps_version(client: TestClient) -> None:
    created = _create(client)
    response = client.patch(
        f"/processes/{created['id']}", json={"executions_per_month": 500, "hourly_cost": None}
    )
    assert response.status_code == 200
    body = response.json()
    assert body["executions_per_month"] == 500
    assert body["hourly_cost"] is None
    assert body["version"] == 2


def test_update_rejects_null_required_field(client: TestClient) -> None:
    created = _create(client)
    response = client.patch(f"/processes/{created['id']}", json={"name": None})
    assert response.status_code == 400


def test_delete_process(client: TestClient) -> None:
    created = _create(client)
    assert client.delete(f"/processes/{created['id']}").status_code == 204
    assert client.get(f"/processes/{created['id']}").status_code == 404


def test_steps_crud_and_order(client: TestClient) -> None:
    created = _create(client)
    pid = created["id"]
    first = created["steps"][0]["id"]

    body = client.post(f"/processes/{pid}/steps", json=step_payload(name="Approve")).json()
    body = client.post(
        f"/processes/{pid}/steps", json=step_payload(name="Download", position=1)
    ).json()
    assert [s["name"] for s in body["steps"]] == ["Download", "Extract invoice fields", "Approve"]
    assert [s["position"] for s in body["steps"]] == [1, 2, 3]

    ids = [s["id"] for s in body["steps"]]
    body = client.put(f"/processes/{pid}/steps/order", json={"step_ids": ids[::-1]}).json()
    assert [s["name"] for s in body["steps"]] == ["Approve", "Extract invoice fields", "Download"]

    body = client.patch(
        f"/steps/{first}", json={"occurrence_rate": "0.5", "criticality": "HIGH"}
    ).json()
    updated = next(s for s in body["steps"] if s["id"] == first)
    assert updated["occurrence_rate"] == "0.5"
    assert updated["criticality"] == "HIGH"

    body = client.delete(f"/steps/{first}").json()
    assert [s["position"] for s in body["steps"]] == [1, 2]
    assert first not in [s["id"] for s in body["steps"]]


def test_reorder_requires_every_step(client: TestClient) -> None:
    created = _create(client)
    response = client.put(f"/processes/{created['id']}/steps/order", json={"step_ids": []})
    assert response.status_code == 400


def test_validation_errors_are_explicit(client: TestClient) -> None:
    response = client.post(
        "/processes", json=process_payload(steps=[step_payload(occurrence_rate="1.2")])
    )
    assert response.status_code == 422
    assert "occurrence_rate" in response.text

    assert (
        client.post("/processes", json=process_payload(executions_per_month=-1)).status_code == 422
    )


def test_unknown_ids_return_404(client: TestClient) -> None:
    missing = "00000000-0000-0000-0000-000000000000"
    assert client.get(f"/processes/{missing}").status_code == 404
    assert client.patch(f"/steps/{missing}", json={"name": "x"}).status_code == 404
    assert client.post(f"/processes/{missing}/analyses", json={}).status_code == 404


def test_demo_processes_load(client: TestClient) -> None:
    demos = client.get("/demo-processes").json()
    assert {d["slug"] for d in demos} == {
        "invoice-intake",
        "customer-onboarding",
        "bank-reconciliation",
    }
    for demo in demos:
        response = client.post(f"/demo-processes/{demo['slug']}")
        assert response.status_code == 201, response.text
    assert client.post("/demo-processes/nope").status_code == 404
