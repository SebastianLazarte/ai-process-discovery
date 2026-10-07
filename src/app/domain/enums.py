from enum import StrEnum


class Level(StrEnum):
    """Ordinal level used for repetitiveness, rule clarity and criticality."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    UNKNOWN = "UNKNOWN"


class InputType(StrEnum):
    DIGITAL_STRUCTURED = "DIGITAL_STRUCTURED"
    DIGITAL_UNSTRUCTURED = "DIGITAL_UNSTRUCTURED"
    PHYSICAL = "PHYSICAL"
    MIXED = "MIXED"
    UNKNOWN = "UNKNOWN"


class IntegrationReadiness(StrEnum):
    NONE = "NONE"
    PARTIAL = "PARTIAL"
    GOOD = "GOOD"
    UNKNOWN = "UNKNOWN"


class AutomationMethod(StrEnum):
    RULE_BASED = "RULE_BASED"
    API_INTEGRATION = "API_INTEGRATION"
    AI_CANDIDATE = "AI_CANDIDATE"
    HYBRID = "HYBRID"
    MANUAL = "MANUAL"
    NEEDS_REVIEW = "NEEDS_REVIEW"


class HumanControl(StrEnum):
    """How much human control a step keeps. Ordered from weakest to strongest."""

    NONE = "NONE"
    RECOMMENDED = "RECOMMENDED"
    REQUIRED = "REQUIRED"

    @property
    def rank(self) -> int:
        return _HUMAN_CONTROL_RANK[self]

    @classmethod
    def strongest(cls, *controls: "HumanControl") -> "HumanControl":
        return max(controls, key=lambda control: control.rank)


_HUMAN_CONTROL_RANK = {
    HumanControl.NONE: 0,
    HumanControl.RECOMMENDED: 1,
    HumanControl.REQUIRED: 2,
}
