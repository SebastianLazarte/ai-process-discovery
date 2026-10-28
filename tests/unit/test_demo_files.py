"""Every demo file is a valid process whose assumptions name its own steps (RS-89)."""

from decimal import Decimal
from typing import Any

import pytest

from app.models.schemas.analysis import BusinessCaseInput
from app.models.schemas.process import ProcessCreate
from app.services.demo_service import demo_files

DEMOS = demo_files()


@pytest.mark.req("RS-89")
def test_there_are_demos() -> None:
    assert DEMOS


@pytest.mark.req("RS-89", criterion=3)
@pytest.mark.parametrize("slug", sorted(DEMOS))
def test_assumptions_only_name_steps_of_the_demo(slug: str) -> None:
    demo: dict[str, Any] = dict(DEMOS[slug])
    preset = demo.pop("assumptions")
    process = ProcessCreate.model_validate(demo)
    names = [step.name for step in process.steps]

    assert len(names) == len(set(names)), "step names must be unique to key the reductions"
    assert set(preset["expected_time_reduction_by_step"]) <= set(names)
    BusinessCaseInput.model_validate({**preset, "expected_time_reduction_by_step": {}})
    for reduction in preset["expected_time_reduction_by_step"].values():
        assert 0 <= Decimal(reduction) <= 1
