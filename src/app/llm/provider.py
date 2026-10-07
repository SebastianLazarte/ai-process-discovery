from typing import Protocol

from app.llm.schemas import LLMAnalysisOutput, LLMAnalysisRequest


class LLMProviderError(Exception):
    """Base for every provider failure. Services only ever catch this family."""

    kind = "provider_error"


class LLMTimeoutError(LLMProviderError):
    kind = "timeout"


class LLMSchemaError(LLMProviderError):
    """The model answered, but not with data matching ``LLMAnalysisOutput``."""

    kind = "invalid_output"


class LLMRefusalError(LLMProviderError):
    kind = "refusal"


class LLMConfigurationError(LLMProviderError):
    kind = "configuration"


class LLMProvider(Protocol):
    """What the analysis service needs from any model provider."""

    @property
    def name(self) -> str: ...

    @property
    def model(self) -> str: ...

    def analyze_process(self, request: LLMAnalysisRequest) -> LLMAnalysisOutput: ...
