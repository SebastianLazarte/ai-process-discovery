"""Demo processes come with preset assumptions and a first analysis (RS-89)."""

from collections.abc import Callable
from decimal import Decimal
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.llm.providers.fake import FakeLLMProvider
from app.services import demo_service

SLUGS = ("distributor-orders", "warranty-claims", "zoning-quotes")


def _load(client: TestClient, slug: str) -> dict[str, Any]:
    response = client.post(f"/api/demo-processes/{slug}")
    assert response.status_code == 201, response.text
    process: dict[str, Any] = response.json()
    return process


@pytest.mark.req("RS-89", criterion=1)
@pytest.mark.parametrize("slug", SLUGS)
def test_a_demo_comes_with_an_analysis_of_its_assumptions(client: TestClient, slug: str) -> None:
    process = _load(client, slug)
    history = client.get(f"/api/processes/{process['id']}/analyses").json()
    assert len(history) == 1

    analysis = client.get(f"/api/analyses/{history[0]['id']}").json()
    impact = analysis["business_impact"]
    assert Decimal(impact["net_monthly_savings"]) > 0
    assert impact["payback_months"] is not None
    assert set(impact["assumptions"]["expected_time_reduction_by_step"]) == {
        step["id"] for step in process["steps"]
    }


@pytest.mark.req("RS-89", criterion=2)
def test_the_first_analysis_never_calls_the_llm_nor_uses_the_quota(
    make_client: Callable[..., TestClient],
) -> None:
    provider = FakeLLMProvider()
    client = make_client(provider, llm_daily_limit=1)
    process = _load(client, "warranty-claims")

    [first] = client.get(f"/api/processes/{process['id']}/analyses").json()
    assert first["llm_status"] == "not_requested"
    assert provider.calls == []

    response = client.post(
        f"/api/processes/{process['id']}/analyses",
        json={"use_llm": True, "confirm_sensitive": True},
    )
    assert response.json()["llm"]["status"] == "ok"


@pytest.mark.req("RS-89", criterion=1)
def test_a_demo_without_assumptions_has_no_analysis(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    demo = demo_service.demo_files()["warranty-claims"]
    del demo["assumptions"]
    monkeypatch.setattr(demo_service, "demo_files", lambda: {"plain": demo})

    process = _load(client, "plain")
    assert client.get(f"/api/processes/{process['id']}/analyses").json() == []
