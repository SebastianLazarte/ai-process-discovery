"""AnthropicProvider with a stubbed SDK client: no network, no key (RS-29)."""

from types import SimpleNamespace
from typing import Any

import anthropic
import httpx2
import pytest
from pydantic import BaseModel, ValidationError

from app.core.config import Settings
from app.llm.provider import (
    LLMConfigurationError,
    LLMProviderError,
    LLMRefusalError,
    LLMSchemaError,
    LLMTimeoutError,
)
from app.llm.providers import build_provider
from app.llm.providers.anthropic import AnthropicProvider
from app.llm.providers.fake import FakeLLMProvider
from app.llm.schemas import LLMAnalysisOutput, LLMAnalysisRequest

REQUEST = LLMAnalysisRequest(process_name="P", process_description="D", steps=[])
VALID = LLMAnalysisOutput(
    step_assessments=[], architecture_recommendations=[], process_risks=[], unknowns=[]
)


class _Messages:
    def __init__(self, outcome: Any) -> None:
        self.outcome = outcome
        self.kwargs: dict[str, Any] = {}

    def parse(self, **kwargs: Any) -> Any:
        self.kwargs = kwargs
        if isinstance(self.outcome, BaseException):
            raise self.outcome
        return self.outcome


def _provider(outcome: Any) -> tuple[AnthropicProvider, _Messages]:
    messages = _Messages(outcome)
    client = SimpleNamespace(beta=SimpleNamespace(messages=messages))
    return AnthropicProvider(client, "claude-opus-5"), messages  # type: ignore[arg-type]


def _response(stop_reason: str = "end_turn", parsed: LLMAnalysisOutput | None = VALID) -> Any:
    return SimpleNamespace(
        model="claude-opus-5",
        stop_reason=stop_reason,
        usage=SimpleNamespace(input_tokens=10, output_tokens=20),
        parsed_output=parsed,
    )


def _http_response(status: int) -> httpx2.Response:
    return httpx2.Response(status, request=httpx2.Request("POST", "https://api.anthropic.com"))


def _validation_error() -> ValidationError:
    class Model(BaseModel):
        x: int

    try:
        Model.model_validate({"x": "not a number"})
    except ValidationError as exc:
        return exc
    raise AssertionError


def test_valid_output_is_accepted_and_request_is_structured() -> None:
    provider, messages = _provider(_response())
    assert provider.analyze_process(REQUEST) == VALID
    assert messages.kwargs["output_format"] is LLMAnalysisOutput
    assert messages.kwargs["model"] == "claude-opus-5"
    assert messages.kwargs["fallbacks"] == "default"
    assert provider.name == "anthropic"
    assert provider.model == "claude-opus-5"


@pytest.mark.parametrize(
    ("outcome", "error"),
    [
        (_validation_error(), LLMSchemaError),
        (_response(stop_reason="refusal"), LLMRefusalError),
        (_response(stop_reason="max_tokens"), LLMSchemaError),
        (_response(parsed=None), LLMSchemaError),
        (anthropic.APITimeoutError(httpx2.Request("POST", "https://x")), LLMTimeoutError),
        (
            anthropic.AuthenticationError("bad key", response=_http_response(401), body=None),
            LLMConfigurationError,
        ),
        (
            anthropic.RateLimitError("slow down", response=_http_response(429), body=None),
            LLMProviderError,
        ),
        (
            anthropic.InternalServerError("boom", response=_http_response(500), body=None),
            LLMProviderError,
        ),
        (
            anthropic.APIConnectionError(request=httpx2.Request("POST", "https://x")),
            LLMProviderError,
        ),
    ],
)
def test_failures_are_normalised(outcome: Any, error: type[LLMProviderError]) -> None:
    provider, _ = _provider(outcome)
    with pytest.raises(error):
        provider.analyze_process(REQUEST)


def test_build_provider_picks_the_configured_adapter() -> None:
    assert isinstance(build_provider(Settings(llm_provider="fake")), FakeLLMProvider)
    provider = build_provider(Settings(llm_provider="anthropic", anthropic_api_key="test-key"))  # type: ignore[arg-type]
    assert isinstance(provider, AnthropicProvider)
