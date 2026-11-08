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


class StepFrequency(StrEnum):
    """How often an execution goes through a step, in the words a person can answer (RS-115)."""

    ALWAYS = "ALWAYS"
    MOST_OF_THE_TIME = "MOST_OF_THE_TIME"
    HALF_OF_THE_TIME = "HALF_OF_THE_TIME"
    SOMETIMES = "SOMETIMES"
    RARELY = "RARELY"


class ExceptionFrequency(StrEnum):
    """How often a step goes off the normal path, in plain words (RS-115)."""

    ALMOST_NEVER = "ALMOST_NEVER"
    SOMETIMES = "SOMETIMES"
    OFTEN = "OFTEN"
    ALMOST_ALWAYS = "ALMOST_ALWAYS"
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
