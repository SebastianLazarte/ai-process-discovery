"""Every catalog template is a valid set of qualitative steps without a single number (RS-95)."""

from typing import Any

import pytest
from pydantic import ValidationError

from app.domain.enums import InputType, IntegrationReadiness, Level
from app.models.schemas.process import StepTraits
from app.models.schemas.template import ProcessTemplate, SectorTemplates
from app.services.template_service import catalog_files

CATALOG = catalog_files()
TEMPLATES = [
    (sector_id, template)
    for sector_id, sector in CATALOG.items()
    for template in sector["templates"]
]
# The person types every number for their company; a template never suggests one.
NUMBERS = {
    "minutes_per_execution",
    "occurrence_rate",
    "exception_rate",
    "executions_per_month",
    "hourly_cost",
}
STEP = {"name": "Check the request", "repetitiveness": "HIGH", "criticality": "LOW"}


def _keys(value: Any) -> set[str]:
    if isinstance(value, dict):
        return set(value) | {key for item in value.values() for key in _keys(item)}
    if isinstance(value, list):
        return {key for item in value for key in _keys(item)}
    return set()


def _numbers(value: Any) -> list[Any]:
    if isinstance(value, dict):
        return [number for item in value.values() for number in _numbers(item)]
    if isinstance(value, list):
        return [number for item in value for number in _numbers(item)]
    is_number = isinstance(value, int | float) and not isinstance(value, bool)
    return [value] if is_number else []


def _ids(cases: list[tuple[str, dict[str, Any]]]) -> list[str]:
    return [f"{sector_id}/{template['slug']}" for sector_id, template in cases]


def test_there_are_templates() -> None:
    assert TEMPLATES


@pytest.mark.parametrize("sector_id", sorted(CATALOG))
def test_every_sector_validates_against_the_contract(sector_id: str) -> None:
    sector = SectorTemplates.model_validate({"id": sector_id, **CATALOG[sector_id]})
    assert sector.name


@pytest.mark.parametrize(("sector_id", "template"), TEMPLATES, ids=_ids(TEMPLATES))
def test_a_template_has_four_to_seven_uniquely_named_steps(
    sector_id: str, template: dict[str, Any]
) -> None:
    names = [step["name"] for step in template["steps"]]
    assert 4 <= len(names) <= 7, sector_id
    assert len(names) == len(set(names))


def test_template_slugs_are_unique_across_the_catalog() -> None:
    slugs = [template["slug"] for _, template in TEMPLATES]
    assert len(slugs) == len(set(slugs))


def test_step_traits_take_their_values_from_the_domain_enums() -> None:
    fields = StepTraits.model_fields
    assert fields["repetitiveness"].annotation is Level
    assert fields["rule_clarity"].annotation is Level
    assert fields["criticality"].annotation is Level
    assert fields["input_type"].annotation is InputType
    assert fields["integration_readiness"].annotation is IntegrationReadiness


@pytest.mark.parametrize(
    ("field", "value"),
    [("repetitiveness", "VERY_HIGH"), ("input_type", "PAPER"), ("integration_readiness", "FULL")],
)
def test_a_value_outside_the_domain_enums_is_rejected(field: str, value: str) -> None:
    with pytest.raises(ValidationError):
        StepTraits.model_validate({**STEP, field: value})


@pytest.mark.parametrize(("sector_id", "template"), TEMPLATES, ids=_ids(TEMPLATES))
def test_a_template_carries_no_numbers(sector_id: str, template: dict[str, Any]) -> None:
    assert not _keys(template) & NUMBERS, sector_id
    assert _numbers(template) == []


@pytest.mark.parametrize("field", sorted(NUMBERS))
def test_the_contract_rejects_a_number_in_a_template(field: str) -> None:
    with pytest.raises(ValidationError):
        StepTraits.model_validate({**STEP, field: "4"})
    with pytest.raises(ValidationError):
        ProcessTemplate.model_validate(
            {"slug": "intake", "name": "Intake", "steps": [STEP], field: "4"}
        )


def test_the_contract_has_no_field_for_a_number() -> None:
    schema = SectorTemplates.model_json_schema()
    assert not _keys(schema) & NUMBERS
