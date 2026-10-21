from functools import lru_cache
from typing import Literal

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

DEFAULT_ANTHROPIC_MODEL = "claude-opus-5"


class Settings(BaseSettings):
    """Runtime configuration. Every value comes from the environment or a local .env file."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "sqlite:///./apd.sqlite"
    # Local runs and tests create missing tables on startup. Production sets it to false:
    # Alembic owns the schema there and runs before a new version starts (ADR 0008).
    create_schema_on_startup: bool = True

    llm_provider: Literal["fake", "anthropic"] = "fake"
    anthropic_api_key: SecretStr | None = None
    anthropic_model: str = DEFAULT_ANTHROPIC_MODEL
    llm_timeout_seconds: float = 60.0
    llm_max_retries: int = 2
    # Analyses that may ask the LLM per UTC day, across every instance. None means no limit.
    llm_daily_limit: int | None = Field(default=None, ge=0)

    log_level: str = "INFO"

    # Public deployment (ADR 0008): the web client warns that data is public and short-lived.
    public_demo: bool = False


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    if not settings.anthropic_model:
        settings.anthropic_model = DEFAULT_ANTHROPIC_MODEL
    return settings
