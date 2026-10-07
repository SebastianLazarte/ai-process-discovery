"""Small builders for domain objects used across tests."""

from decimal import Decimal
from typing import Any

from app.domain.entities import Process, ProcessStep
from app.domain.enums import InputType, IntegrationReadiness, Level


def make_step(**overrides: Any) -> ProcessStep:
    values: dict[str, Any] = {
        "name": "Step",
        "minutes_per_execution": Decimal(6),
        "repetitiveness": Level.MEDIUM,
        "rule_clarity": Level.MEDIUM,
        "input_type": InputType.DIGITAL_STRUCTURED,
        "exception_rate": Decimal("0.05"),
        "integration_readiness": IntegrationReadiness.PARTIAL,
        "criticality": Level.MEDIUM,
    }
    values.update(overrides)
    return ProcessStep(**values)


def make_process(*steps: ProcessStep, **overrides: Any) -> Process:
    positioned = tuple(
        step if step.position != 1 or index == 0 else _with_position(step, index + 1)
        for index, step in enumerate(steps)
    )
    values: dict[str, Any] = {
        "name": "Process",
        "executions_per_month": 10,
        "steps": positioned,
    }
    values.update(overrides)
    return Process(**values)


def invoice_process() -> Process:
    """The worked example from the design report: 400 invoices a month at 18.50/hour."""
    return Process(
        name="Invoice intake and validation",
        description="Supplier invoices received by email and keyed into the ERP",
        owner="Finance Operations",
        executions_per_month=400,
        hourly_cost=Decimal("18.50"),
        steps=(
            ProcessStep(
                name="Extract invoice fields",
                description="Copy data from an invoice received by email into the ERP",
                responsible_role="Finance Assistant",
                tools=("Email", "ERP"),
                input_description="PDF invoice",
                output_description="ERP invoice record",
                minutes_per_execution=Decimal("4.0"),
                occurrence_rate=Decimal("1.0"),
                repetitiveness=Level.HIGH,
                rule_clarity=Level.MEDIUM,
                input_type=InputType.DIGITAL_UNSTRUCTURED,
                exception_rate=Decimal("0.08"),
                integration_readiness=IntegrationReadiness.GOOD,
                handles_sensitive_data=True,
                criticality=Level.MEDIUM,
                problems=("manual data entry", "typing errors"),
            ),
        ),
    )


def _with_position(step: ProcessStep, position: int) -> ProcessStep:
    from dataclasses import replace

    return replace(step, position=position)
