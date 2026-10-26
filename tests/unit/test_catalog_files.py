"""Every catalog template is a valid set of qualitative steps without a single number (RS-95).

The catalog covers seven sectors with three processes each, named after generic roles and
tools, and `docs/design/catalog.md` names the sources of each sector (RS-97).
"""

import re
from pathlib import Path
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
# The sectors and processes approved by the Product Owner for RS-97.
SECTORS = {
    "Manufacturing": [
        "Supplier invoice processing",
        "Purchase orders to suppliers",
        "Customer order entry",
    ],
    "Retail and e-commerce": [
        "Returns and refunds",
        "Inventory reconciliation",
        "Customer support requests",
    ],
    "Logistics": ["Freight invoice audit", "Shipment status updates", "Customs documentation"],
    "Banking and financial services": [
        "Customer onboarding and KYC",
        "Account reconciliation",
        "Loan application processing",
    ],
    "Insurance": ["Claims intake (first notice of loss)", "Policy changes", "Quote preparation"],
    "Healthcare administration": [
        "Patient intake and registration",
        "Appointment scheduling",
        "Insurance claims submission",
    ],
    "Any sector": ["Employee onboarding", "Expense reports", "Customer support requests"],
}
# Vendors a business process often names. Templates use generic tools ("ERP", "Help desk").
BRANDS = [
    "Amazon", "DHL", "DocuSign", "Epic", "Excel", "FedEx", "Gmail", "Google",
    "Guidewire", "HubSpot", "Jira", "Maersk", "Mastercard", "Microsoft", "NetSuite", "Oracle",
    "Outlook", "PayPal", "QuickBooks", "Salesforce", "SAP", "ServiceNow", "SharePoint",
    "Shopify", "Slack", "Stripe", "UPS", "Visa", "Workday", "Xero", "Zendesk",
]  # fmt: skip
BRAND = re.compile(rf"\b({'|'.join(BRANDS)})\b", re.IGNORECASE)
CATALOG_DOC = Path(__file__).resolve().parents[2] / "docs" / "design" / "catalog.md"


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


def _texts(value: Any) -> list[str]:
    if isinstance(value, dict):
        return [text for item in value.values() for text in _texts(item)]
    if isinstance(value, list):
        return [text for item in value for text in _texts(item)]
    return [value] if isinstance(value, str) else []


def _doc_sections() -> dict[str, str]:
    parts = re.split(r"^## (.+)$", CATALOG_DOC.read_text(encoding="utf-8"), flags=re.MULTILINE)
    return dict(zip(parts[1::2], parts[2::2], strict=True))


def test_the_catalog_has_seven_sectors_with_three_processes_each() -> None:
    listed = {
        sector["name"]: [template["name"] for template in sector["templates"]]
        for sector in CATALOG.values()
    }

    assert listed == SECTORS


@pytest.mark.parametrize(("sector_id", "template"), TEMPLATES, ids=_ids(TEMPLATES))
def test_a_template_names_no_real_company(sector_id: str, template: dict[str, Any]) -> None:
    named = [match for text in _texts(template) for match in BRAND.findall(text)]

    assert named == [], sector_id


@pytest.mark.parametrize("text", ["Send the invoice by Outlook", "Book it in sap", "Visa check"])
def test_a_brand_in_a_template_is_caught(text: str) -> None:
    assert BRAND.search(text)


@pytest.mark.parametrize("sector", sorted(SECTORS))
def test_the_design_docs_name_the_sources_of_each_sector(sector: str) -> None:
    section = _doc_sections()[sector]

    for process in SECTORS[sector]:
        row = next(line for line in section.splitlines() if line.startswith(f"| {process} |"))
        assert re.search(r"\]\(https://[^)]+\)", row), process
