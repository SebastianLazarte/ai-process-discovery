# ADR 0004: Provider-agnostic LLM layer, Anthropic first

**Status:** accepted · 2026-10-07

## Decision

- Services depend on the `LLMProvider` protocol (`app/llm/provider.py`), never on an SDK.
- `FakeLLMProvider` is deterministic and is the default, so the demo and CI run without a key.
- `AnthropicProvider` is the first real adapter. It uses the SDK's structured output (`beta.messages.parse` with `output_format=LLMAnalysisOutput`), so the response is validated against the same Pydantic model the rest of the code uses. It enables server-side refusal fallbacks (`fallbacks="default"`), sets a timeout and a limited number of retries, and maps every SDK error to `LLMProviderError` subclasses: timeout, invalid output, refusal, configuration.
- The prompt has a version (`PROMPT_VERSION`) stored with each analysis. Full prompts are never logged.
- Before any step flagged as sensitive is sent to the provider, the API requires `confirm_sensitive=true`.

## Consequences

- A second provider is one new module implementing `name`, `model` and `analyze_process`.
- Provider outages degrade the analysis instead of failing it.

## Alternatives rejected

- **Two providers from day one.** The report recommends one real adapter and an interface ready for the second. Building both shows little more.
