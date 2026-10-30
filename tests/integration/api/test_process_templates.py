"""The process template catalog is served grouped by sector, without numbers (RS-95)."""

from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.services.template_service import catalog_files


def _sectors(client: TestClient) -> list[dict[str, Any]]:
    response = client.get("/api/process-templates")
    assert response.status_code == 200, response.text
    sectors: list[dict[str, Any]] = response.json()
    return sectors


def test_templates_are_grouped_by_sector_with_name_and_description(client: TestClient) -> None:
    sectors = _sectors(client)

    assert [sector["id"] for sector in sectors] == list(catalog_files())
    for sector in sectors:
        assert sector["name"]
        for template in sector["templates"]:
            assert template["slug"]
            assert template["name"]
            assert template["description"]
            assert template["steps"]


def test_any_sector_offers_the_common_back_office_processes(client: TestClient) -> None:
    sectors = {sector["id"]: sector for sector in _sectors(client)}

    any_sector = sectors["any-sector"]
    assert any_sector["name"] == "Any sector"
    assert [template["name"] for template in any_sector["templates"]] == [
        "Employee onboarding",
        "Expense reports",
        "Customer support requests",
    ]


def test_a_template_step_is_served_with_its_traits_and_no_numbers(client: TestClient) -> None:
    [first_sector, *_] = _sectors(client)
    step = first_sector["templates"][0]["steps"][0]

    assert {"name", "repetitiveness", "rule_clarity", "input_type", "criticality"} <= set(step)
    assert not {"minutes_per_execution", "occurrence_rate", "exception_rate"} & set(step)
    assert not {"executions_per_month", "hourly_cost"} & set(first_sector["templates"][0])


def test_the_catalog_answers_only_under_api(client: TestClient) -> None:
    assert client.get("/process-templates").status_code == 404


@pytest.mark.req("RS-96", criterion=3)
def test_every_template_creates_a_process_in_one_request(client: TestClient) -> None:
    # What the review screen sends: the template's traits as they are, plus the figures
    # the person typed. Each template must pass the process contract unchanged.
    for sector in _sectors(client):
        for template in sector["templates"]:
            body = {
                "name": template["name"],
                "description": template["description"],
                "executions_per_month": 200,
                "steps": [
                    {**traits, "minutes_per_execution": "5", "occurrence_rate": "1"}
                    for traits in template["steps"]
                ],
            }

            response = client.post("/api/processes", json=body)

            assert response.status_code == 201, (sector["id"], template["slug"], response.text)
            steps = response.json()["steps"]
            assert [step["name"] for step in steps] == [t["name"] for t in template["steps"]]
            for step, traits in zip(steps, template["steps"], strict=True):
                assert {key: step[key] for key in traits} == traits
