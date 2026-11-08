"""Frequency and exceptions said in plain words (RS-115).

A choice turns into its rate through the capture policy, and the step keeps the choice.
A rate sent on its own stays an exact figure, as in the demos.
"""

import pytest
from fastapi.testclient import TestClient

from tests.payloads import process_payload, step_payload


def _create(client: TestClient, **step: object) -> dict:  # type: ignore[type-arg]
    payload = step_payload()
    del payload["exception_rate"]
    payload.update(step)
    response = client.post("/api/processes", json=process_payload(steps=[payload]))
    assert response.status_code == 201, response.text
    return response.json()  # type: ignore[no-any-return]


@pytest.mark.req("RS-115", criterion=2)
def test_a_choice_sets_the_rate_the_analysis_uses_and_is_kept(client: TestClient) -> None:
    process = _create(client, frequency="SOMETIMES", exception_frequency="ALMOST_NEVER")
    (step,) = process["steps"]
    assert (step["frequency"], step["occurrence_rate"]) == ("SOMETIMES", "0.25")
    assert (step["exception_frequency"], step["exception_rate"]) == ("ALMOST_NEVER", "0.02")

    response = client.post(f"/api/processes/{process['id']}/analyses", json={})
    assert response.status_code == 201, response.text
    (assessment,) = response.json()["step_assessments"]
    # 400 executions, a quarter of them through the step, 4 minutes each: 400 minutes.
    assert assessment["monthly_hours"] == "6.67"

    body = client.patch(f"/api/steps/{step['id']}", json={"frequency": "RARELY"}).json()
    (updated,) = body["steps"]
    assert (updated["frequency"], updated["occurrence_rate"]) == ("RARELY", "0.1")
    assert updated["exception_frequency"] == "ALMOST_NEVER"


def test_dont_know_keeps_the_exception_rate_unknown(client: TestClient) -> None:
    (step,) = _create(client, exception_frequency="UNKNOWN")["steps"]
    assert step["exception_rate"] is None


def test_a_new_step_without_figures_says_always_and_dont_know(client: TestClient) -> None:
    (step,) = _create(client)["steps"]
    assert (step["frequency"], step["occurrence_rate"]) == ("ALWAYS", "1")
    assert (step["exception_frequency"], step["exception_rate"]) == ("UNKNOWN", None)


def test_a_rate_sent_alone_is_an_exact_figure_with_no_choice(client: TestClient) -> None:
    (step,) = _create(client, occurrence_rate="0.45", exception_rate="0.06")["steps"]
    assert (step["frequency"], step["occurrence_rate"]) == (None, "0.45")
    assert (step["exception_frequency"], step["exception_rate"]) == (None, "0.06")

    body = client.patch(f"/api/steps/{step['id']}", json={"criticality": "HIGH"}).json()
    (kept,) = body["steps"]
    assert (kept["frequency"], kept["occurrence_rate"]) == (None, "0.45")


@pytest.mark.req("RS-115", criterion=4)
@pytest.mark.parametrize(
    ("choice", "rate"),
    [("frequency", "occurrence_rate"), ("exception_frequency", "exception_rate")],
)
def test_a_choice_and_a_rate_together_return_422_naming_the_rate(
    client: TestClient, choice: str, rate: str
) -> None:
    values = {"frequency": "HALF_OF_THE_TIME", "exception_frequency": "OFTEN"}
    step = step_payload(**{choice: values[choice], rate: "0.5"})
    created = client.post("/api/processes", json=process_payload(steps=[step]))
    assert created.status_code == 422
    assert [error["loc"][-1] for error in created.json()["detail"]] == [rate]

    (existing,) = _create(client)["steps"]
    patched = client.patch(
        f"/api/steps/{existing['id']}", json={choice: values[choice], rate: "0.5"}
    )
    assert patched.status_code == 422
    assert rate in patched.text
