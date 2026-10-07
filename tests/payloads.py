"""Request payload builders shared by the API tests."""

from typing import Any


def step_payload(**overrides: Any) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "name": "Extract invoice fields",
        "minutes_per_execution": "4.0",
        "repetitiveness": "HIGH",
        "rule_clarity": "MEDIUM",
        "input_type": "DIGITAL_UNSTRUCTURED",
        "exception_rate": "0.08",
        "integration_readiness": "GOOD",
        "handles_sensitive_data": False,
        "criticality": "MEDIUM",
    }
    payload.update(overrides)
    return payload


def process_payload(**overrides: Any) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "name": "Invoice intake",
        "description": "Invoices keyed into the ERP",
        "owner": "Finance",
        "executions_per_month": 400,
        "hourly_cost": "18.50",
        "steps": [step_payload()],
    }
    payload.update(overrides)
    return payload
