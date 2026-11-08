"""Scoring policy: the weights and thresholds the scoring engine applies.

The values are a product decision, not a scientific truth. They live here, versioned,
so they can change without touching the algorithm in ``scoring.py``.
"""

from collections.abc import Mapping
from dataclasses import dataclass
from decimal import Decimal
from types import MappingProxyType

from app.domain.enums import (
    ExceptionFrequency,
    InputType,
    IntegrationReadiness,
    Level,
    StepFrequency,
)


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


@dataclass(frozen=True, slots=True, kw_only=True)
class CapturePolicy:
    """The rate each plain-word answer stands for when a step is captured (RS-115).

    A person rarely knows that a step runs in 0.45 of executions, but can say "half of
    the time". The words are what they answer; these rates are what the formulas use.
    Like the scoring weights, they are a product decision, versioned here.
    """

    version: str
    occurrence_rates: Mapping[StepFrequency, Decimal]
    exception_rates: Mapping[ExceptionFrequency, Decimal | None]

    def occurrence_rate(self, frequency: StepFrequency) -> Decimal:
        return self.occurrence_rates[frequency]

    def exception_rate(self, exceptions: ExceptionFrequency) -> Decimal | None:
        """``None`` for UNKNOWN: an unknown rate stays unknown, never zero."""
        return self.exception_rates[exceptions]


# Each rate sits inside one scoring band, so the word decides the band. "Sometimes" is
# exactly the RULE_BASED limit (0.10): a step that goes off the path about 1 in 10 times
# can still run on rules. "Often" (about 1 in 3) is past every exception ceiling.
CAPTURE_POLICY_V1 = CapturePolicy(
    version="capture-v1",
    occurrence_rates=MappingProxyType(
        {
            StepFrequency.ALWAYS: Decimal(1),
            StepFrequency.MOST_OF_THE_TIME: Decimal("0.75"),
            StepFrequency.HALF_OF_THE_TIME: Decimal("0.5"),
            StepFrequency.SOMETIMES: Decimal("0.25"),
            StepFrequency.RARELY: Decimal("0.1"),
        }
    ),
    exception_rates=MappingProxyType(
        {
            ExceptionFrequency.ALMOST_NEVER: Decimal("0.02"),
            ExceptionFrequency.SOMETIMES: Decimal("0.1"),
            ExceptionFrequency.OFTEN: Decimal("0.33"),
            ExceptionFrequency.ALMOST_ALWAYS: Decimal("0.8"),
            ExceptionFrequency.UNKNOWN: None,
        }
    ),
)

DEFAULT_CAPTURE_POLICY = CAPTURE_POLICY_V1
