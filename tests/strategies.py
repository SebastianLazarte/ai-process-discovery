"""Hypothesis strategies that build valid domain objects for property-based tests."""

from hypothesis import strategies as st

from app.domain.entities import Process, ProcessStep
from app.domain.enums import AutomationMethod, InputType, IntegrationReadiness, Level
from app.domain.reconciliation import AISuggestion

unit_interval = st.decimals(min_value=0, max_value=1, places=2)
minutes = st.decimals(min_value=0, max_value=600, places=2)
money = st.decimals(min_value=0, max_value=100_000, places=2)


@st.composite
def steps(draw: st.DrawFn, position: int = 1) -> ProcessStep:
    return ProcessStep(
        name="Step",
        position=position,
        minutes_per_execution=draw(minutes),
        occurrence_rate=draw(unit_interval),
        repetitiveness=draw(st.sampled_from(Level)),
        rule_clarity=draw(st.sampled_from(Level)),
        input_type=draw(st.sampled_from(InputType)),
        exception_rate=draw(st.none() | unit_interval),
        integration_readiness=draw(st.sampled_from(IntegrationReadiness)),
        requires_human_judgement=draw(st.booleans()),
        requires_human_approval=draw(st.booleans()),
        handles_sensitive_data=draw(st.booleans()),
        criticality=draw(st.sampled_from(Level)),
    )


@st.composite
def processes(draw: st.DrawFn, max_steps: int = 5) -> Process:
    count = draw(st.integers(min_value=1, max_value=max_steps))
    return Process(
        name="Process",
        executions_per_month=draw(st.integers(min_value=0, max_value=10_000)),
        hourly_cost=draw(st.none() | money),
        steps=tuple(draw(steps(position=index + 1)) for index in range(count)),
    )


ai_suggestions = st.builds(
    AISuggestion,
    method=st.sampled_from(AutomationMethod),
    confidence=st.floats(min_value=0, max_value=1),
    interpretation=st.just("i"),
    rationale=st.just("r"),
    human_control_recommended=st.booleans(),
)
