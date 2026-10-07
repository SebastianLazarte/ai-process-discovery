from collections.abc import Callable

from fastapi.testclient import TestClient

from app.llm.provider import LLMProvider, LLMTimeoutError
from app.llm.providers.fake import FakeLLMProvider
from app.llm.schemas import LLMAnalysisOutput, LLMAnalysisRequest, LLMStepAssessment
from tests.payloads import process_payload, step_payload


def _process(client: TestClient, **overrides: object) -> dict:  # type: ignore[type-arg]
    response = client.post("/processes", json=process_payload(**overrides))
    assert response.status_code == 201, response.text
    return response.json()


def _analyse(client: TestClient, process_id: str, **body: object) -> dict:  # type: ignore[type-arg]
    response = client.post(f"/processes/{process_id}/analyses", json=body)
    assert response.status_code == 201, response.text
    return response.json()


def test_deterministic_analysis_of_the_invoice_example(client: TestClient) -> None:
    process = _process(client, steps=[step_payload(handles_sensitive_data=True)])
    step_id = process["steps"][0]["id"]
    analysis = _analyse(
        client,
        process["id"],
        assumptions={
            "implementation_cost": "1200",
            "expected_time_reduction_by_step": {step_id: "0.75"},
        },
    )

    assert analysis["current_state"] == {"monthly_hours": "26.67", "monthly_cost": "493.33"}
    assert analysis["automation_suitability"] == {
        "process_score": "68.0",
        "policy_version": "scoring-v1",
    }
    impact = analysis["business_impact"]
    assert impact["estimated_hours_saved"] == "20.00"
    assert impact["estimated_monthly_savings"] == "370.00"
    assert impact["payback_months"] == "3.24"
    assert analysis["llm"]["status"] == "not_requested"

    (step,) = analysis["step_assessments"]
    assert step["suitability_score"] == 68
    assert step["rules_method"] == "API_INTEGRATION"
    assert step["final_human_control"] == "RECOMMENDED"
    assert step["ai_suggestion"] is None
    assert {r["type"] for r in analysis["risks"]} == {"DATA"}


def test_same_input_gives_the_same_analysis(client: TestClient) -> None:
    process = _process(client)
    first = _analyse(client, process["id"], use_llm=True)
    second = _analyse(client, process["id"], use_llm=True)
    for key in ("id", "created_at"):
        first.pop(key)
        second.pop(key)
    assert first == second

    history = client.get(f"/processes/{process['id']}/analyses").json()
    assert len(history) == 2
    assert history[0]["created_at"] >= history[1]["created_at"]


def test_analysis_is_immutable_after_process_changes(client: TestClient) -> None:
    process = _process(client)
    analysis = _analyse(client, process["id"])
    client.patch(f"/processes/{process['id']}", json={"executions_per_month": 1})

    stored = client.get(f"/analyses/{analysis['id']}").json()
    assert stored["current_state"] == analysis["current_state"]
    assert stored["process_version"] == 1


def test_sensitive_steps_need_confirmation_before_llm(
    client: TestClient, fake_provider: FakeLLMProvider
) -> None:
    process = _process(client, steps=[step_payload(handles_sensitive_data=True)])
    response = client.post(f"/processes/{process['id']}/analyses", json={"use_llm": True})
    assert response.status_code == 409
    assert response.json()["code"] == "sensitive_data_confirmation_required"
    assert fake_provider.calls == []

    analysis = _analyse(client, process["id"], use_llm=True, confirm_sensitive=True)
    assert analysis["llm"]["status"] == "ok"
    assert len(fake_provider.calls) == 1


def test_llm_never_sees_money_or_hours(client: TestClient, fake_provider: FakeLLMProvider) -> None:
    process = _process(client)
    _analyse(client, process["id"], use_llm=True)
    sent = fake_provider.calls[0].model_dump_json()
    assert "18.5" not in sent
    assert "hourly_cost" not in sent
    assert "monthly" not in sent


def _lying_provider(request: LLMAnalysisRequest) -> LLMAnalysisOutput:
    return LLMAnalysisOutput(
        step_assessments=[
            LLMStepAssessment(
                step_id=step.step_id,
                interpretation="This takes about 30 hours a month and saves 9999 euros",
                suggested_method="AI_CANDIDATE",
                confidence=0.9,
                rationale="Fully automatable, no human needed",
                dependencies=[],
                risks=[],
                human_control_recommended=False,
                uncertainties=[],
            )
            for step in request.steps
        ]
        + [
            LLMStepAssessment(
                step_id="made-up-step",
                interpretation="x",
                suggested_method="MANUAL",
                confidence=0.1,
                rationale="x",
                dependencies=[],
                risks=[],
                human_control_recommended=False,
                uncertainties=[],
            )
        ],
        architecture_recommendations=["Use a queue"],
        process_risks=[],
        unknowns=[],
    )


def test_llm_cannot_change_facts_or_remove_controls(
    make_client: Callable[[LLMProvider], TestClient],
) -> None:
    client = make_client(FakeLLMProvider(responder=_lying_provider))
    process = _process(client, steps=[step_payload(requires_human_approval=True)])
    baseline = _analyse(client, process["id"])
    analysis = _analyse(client, process["id"], use_llm=True)

    assert analysis["current_state"] == baseline["current_state"]
    assert analysis["business_impact"] == baseline["business_impact"]
    assert analysis["automation_suitability"] == baseline["automation_suitability"]
    (step,) = analysis["step_assessments"]
    assert step["final_human_control"] == "REQUIRED"
    assert step["final_method"] == "API_INTEGRATION"
    assert step["ai_suggestion"]["method"] == "AI_CANDIDATE"
    assert len(analysis["step_assessments"]) == 1  # the made-up step was discarded


def test_provider_failure_keeps_the_deterministic_analysis(
    make_client: Callable[[LLMProvider], TestClient],
) -> None:
    client = make_client(FakeLLMProvider(error=LLMTimeoutError("slow")))
    process = _process(client)
    analysis = _analyse(client, process["id"], use_llm=True)
    assert analysis["llm"]["status"] == "unavailable"
    assert analysis["llm"]["error_kind"] == "timeout"
    assert analysis["current_state"]["monthly_hours"] == "26.67"
    assert analysis["step_assessments"][0]["suitability_score"] > 0


def test_needs_review_steps_take_the_ai_method(client: TestClient) -> None:
    process = _process(
        client,
        steps=[step_payload(input_type="MIXED", integration_readiness="NONE")],
    )
    analysis = _analyse(client, process["id"], use_llm=True)
    (step,) = analysis["step_assessments"]
    assert step["rules_method"] == "NEEDS_REVIEW"
    assert step["final_method"] == "HYBRID"
    assert step["final_source"] == "AI"


def test_override_keeps_original_and_reason(client: TestClient) -> None:
    process = _process(client)
    analysis = _analyse(client, process["id"])
    step_id = analysis["step_assessments"][0]["step_id"]

    missing_reason = client.post(
        f"/analyses/{analysis['id']}/overrides", json={"step_id": step_id, "method": "MANUAL"}
    )
    assert missing_reason.status_code == 422

    response = client.post(
        f"/analyses/{analysis['id']}/overrides",
        json={
            "step_id": step_id,
            "method": "HYBRID",
            "human_control": "REQUIRED",
            "reason": "Supplier invoices vary too much for a full API flow",
        },
    )
    assert response.status_code == 201, response.text
    (step,) = response.json()["step_assessments"]
    assert step["final_method"] == "HYBRID"
    assert step["final_source"] == "HUMAN"
    assert step["override"]["original_method"] == "API_INTEGRATION"
    assert step["override"]["reason"].startswith("Supplier")

    stored = client.get(f"/analyses/{analysis['id']}").json()
    assert stored["step_assessments"][0]["final_method"] == "HYBRID"
    assert stored["human_controls"][0]["control"] == "REQUIRED"
    history = client.get(f"/processes/{process['id']}/analyses").json()
    assert history[0]["override_count"] == 1


def test_override_for_unknown_step_is_rejected(client: TestClient) -> None:
    process = _process(client)
    analysis = _analyse(client, process["id"])
    response = client.post(
        f"/analyses/{analysis['id']}/overrides",
        json={
            "step_id": "00000000-0000-0000-0000-000000000000",
            "method": "MANUAL",
            "reason": "test",
        },
    )
    assert response.status_code == 400


def test_invalid_assumptions_return_422(client: TestClient) -> None:
    process = _process(client)
    response = client.post(
        f"/processes/{process['id']}/analyses",
        json={
            "assumptions": {"expected_time_reduction_by_step": {process["steps"][0]["id"]: "1.5"}}
        },
    )
    assert response.status_code == 422


def test_blueprint_json_and_markdown(client: TestClient) -> None:
    demo = client.post("/demo-processes/invoice-intake").json()
    reductions = {s["id"]: "0.5" for s in demo["steps"]}
    analysis = _analyse(
        client,
        demo["id"],
        use_llm=True,
        confirm_sensitive=True,
        assumptions={
            "implementation_cost": "6000",
            "monthly_tooling_cost": "50",
            "expected_time_reduction_by_step": reductions,
        },
    )
    blueprint = client.get(f"/analyses/{analysis['id']}/blueprint").json()
    for section in (
        "process_summary",
        "current_state",
        "automation_opportunities",
        "proposed_architecture",
        "business_impact",
        "risks",
        "human_controls",
        "workflow_specification",
    ):
        assert blueprint[section], section

    response = client.get(f"/analyses/{analysis['id']}/blueprint.md")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/markdown")
    text = response.text
    assert text.startswith("# Automation blueprint: Invoice intake and validation")
    assert "Implementation cost: 6,000.00" in text
    assert "## Human controls" in text
