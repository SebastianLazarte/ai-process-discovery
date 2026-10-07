"""Anthropic adapter: structured output validated against ``LLMAnalysisOutput``.

Everything provider-specific stays in this module: SDK client, model, timeouts,
retries, refusal fallbacks and error mapping. Callers only see ``LLMProviderError``.
"""

import logging

import anthropic
from pydantic import ValidationError

from app.core.config import Settings
from app.llm.prompts import SYSTEM_PROMPT, build_user_prompt
from app.llm.provider import (
    LLMConfigurationError,
    LLMProviderError,
    LLMRefusalError,
    LLMSchemaError,
    LLMTimeoutError,
)
from app.llm.schemas import LLMAnalysisOutput, LLMAnalysisRequest

logger = logging.getLogger(__name__)

# Server-side refusal fallback: if a safety classifier declines, the API re-runs the
# request on Anthropic's recommended fallback model inside the same call.
FALLBACK_BETA = "server-side-fallback-2026-07-01"
MAX_OUTPUT_TOKENS = 16000


class AnthropicProvider:
    def __init__(self, client: anthropic.Anthropic, model: str) -> None:
        self._client = client
        self._model = model

    @classmethod
    def from_settings(cls, settings: Settings) -> "AnthropicProvider":
        api_key = (
            settings.anthropic_api_key.get_secret_value() if settings.anthropic_api_key else None
        )
        try:
            client = anthropic.Anthropic(
                # None lets the SDK resolve credentials itself (env var or CLI profile).
                api_key=api_key,
                timeout=settings.llm_timeout_seconds,
                max_retries=settings.llm_max_retries,
            )
        except anthropic.AnthropicError as exc:
            raise LLMConfigurationError(f"cannot create Anthropic client: {exc}") from exc
        return cls(client, settings.anthropic_model)

    @property
    def name(self) -> str:
        return "anthropic"

    @property
    def model(self) -> str:
        return self._model

    def analyze_process(self, request: LLMAnalysisRequest) -> LLMAnalysisOutput:
        try:
            response = self._client.beta.messages.parse(
                model=self._model,
                max_tokens=MAX_OUTPUT_TOKENS,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": build_user_prompt(request)}],
                output_format=LLMAnalysisOutput,
                output_config={"effort": "medium"},
                betas=[FALLBACK_BETA],
                fallbacks="default",
            )
        except ValidationError as exc:
            raise LLMSchemaError(
                f"model output does not match the schema ({exc.error_count()} errors)"
            ) from exc
        except anthropic.APITimeoutError as exc:
            raise LLMTimeoutError("provider timed out") from exc
        except (
            anthropic.AuthenticationError,
            anthropic.PermissionDeniedError,
            anthropic.NotFoundError,
        ) as exc:
            raise LLMConfigurationError(
                f"provider rejected the configuration: {exc.status_code}"
            ) from exc
        except anthropic.RateLimitError as exc:
            raise LLMProviderError("provider rate limit reached") from exc
        except anthropic.APIStatusError as exc:
            raise LLMProviderError(f"provider returned HTTP {exc.status_code}") from exc
        except anthropic.APIConnectionError as exc:
            raise LLMProviderError("cannot reach the provider") from exc

        logger.info(
            "llm_call_completed",
            extra={
                "provider": self.name,
                "model": response.model,
                "stop_reason": response.stop_reason,
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens,
            },
        )

        if response.stop_reason == "refusal":
            raise LLMRefusalError("the model declined the request")
        if response.stop_reason == "max_tokens":
            raise LLMSchemaError("model output was truncated")
        parsed = response.parsed_output
        if parsed is None:
            raise LLMSchemaError("model returned no structured output")
        return parsed
