from app.core.config import Settings
from app.llm.provider import LLMProvider
from app.llm.providers.fake import FakeLLMProvider


def build_provider(settings: Settings) -> LLMProvider:
    if settings.llm_provider == "anthropic":
        from app.llm.providers.anthropic import AnthropicProvider

        return AnthropicProvider.from_settings(settings)
    return FakeLLMProvider()
