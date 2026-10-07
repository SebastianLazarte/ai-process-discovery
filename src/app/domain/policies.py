"""Scoring policy: the weights and thresholds the scoring engine applies.

The values are a product decision, not a scientific truth. They live here, versioned,
so they can change without touching the algorithm in ``scoring.py``.
"""

from collections.abc import Mapping
from dataclasses import dataclass
from decimal import Decimal
from types import MappingProxyType

from app.domain.enums import InputType, IntegrationReadiness, Level


@dataclass(frozen=True, slots=True)
class Band:
    """Awards ``points`` when the measured value is >= ``threshold`` (or <= for ceilings)."""

    threshold: Decimal
    points: int


@dataclass(frozen=True, slots=True, kw_only=True)
class ScoringPolicy:
    version: str

    # Effective executions per month (executions * occurrence_rate), highest band first.
    frequency_floors: tuple[Band, ...]
    repetitiveness_points: Mapping[Level, int]
    rule_clarity_points: Mapping[Level, int]
    input_type_points: Mapping[InputType, int]
    # Exception rate ceilings, lowest ceiling first. Above every ceiling scores 0.
    exception_ceilings: tuple[Band, ...]
    integration_points: Mapping[IntegrationReadiness, int]

    human_judgement_penalty: int
    sensitive_data_penalty: int
    high_criticality_penalty: int

    # Classification thresholds
    rule_based_max_exception_rate: Decimal

    @property
    def max_points(self) -> dict[str, int]:
        return {
            "frequency": max(band.points for band in self.frequency_floors),
            "repetitiveness": max(self.repetitiveness_points.values()),
            "rule_clarity": max(self.rule_clarity_points.values()),
            "input_type": max(self.input_type_points.values()),
            "exception_rate": max(band.points for band in self.exception_ceilings),
            "integration_readiness": max(self.integration_points.values()),
        }


SCORING_POLICY_V1 = ScoringPolicy(
    version="scoring-v1",
    frequency_floors=(
        Band(Decimal(200), 20),
        Band(Decimal(50), 15),
        Band(Decimal(20), 10),
        Band(Decimal(5), 6),
        Band(Decimal(0), 2),
    ),
    repetitiveness_points=MappingProxyType(
        {Level.HIGH: 20, Level.MEDIUM: 10, Level.LOW: 3, Level.UNKNOWN: 0}
    ),
    rule_clarity_points=MappingProxyType(
        {Level.HIGH: 20, Level.MEDIUM: 10, Level.LOW: 3, Level.UNKNOWN: 0}
    ),
    input_type_points=MappingProxyType(
        {
            InputType.DIGITAL_STRUCTURED: 15,
            InputType.DIGITAL_UNSTRUCTURED: 8,
            InputType.MIXED: 5,
            InputType.PHYSICAL: 0,
            InputType.UNKNOWN: 0,
        }
    ),
    exception_ceilings=(
        Band(Decimal("0.05"), 15),
        Band(Decimal("0.15"), 10),
        Band(Decimal("0.30"), 5),
    ),
    integration_points=MappingProxyType(
        {
            IntegrationReadiness.GOOD: 10,
            IntegrationReadiness.PARTIAL: 5,
            IntegrationReadiness.NONE: 0,
            IntegrationReadiness.UNKNOWN: 0,
        }
    ),
    human_judgement_penalty=25,
    sensitive_data_penalty=10,
    high_criticality_penalty=15,
    rule_based_max_exception_rate=Decimal("0.10"),
)

DEFAULT_POLICY = SCORING_POLICY_V1
