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

    # Embeddings for retrieval over the sector catalog (ADR 0021). Fake by default: no key,
    # deterministic. "voyage" needs voyage_api_key and arrives with RS-120.
    embedding_provider: Literal["fake", "voyage"] = "fake"
    voyage_api_key: SecretStr | None = None
    voyage_model: str = "voyage-4-lite"
    # Lowest cosine similarity at which a catalog process is retrieved for a description.
    # Provisional, picked for the fake embedder: pasted catalog descriptions score 0.69 to
    # 0.95 and unrelated sentences 0.23 to 0.51. RS-119 sets it per model from the gold set.
    retrieval_threshold: float = Field(default=0.6, ge=-1.0, le=1.0)

    log_level: str = "INFO"

    # Public deployment (ADR 0008): the web client warns that data is public and short-lived.
    public_demo: bool = False
    # AI drafts of a process from a description (B14). Off until RS-100 and RS-101 merge
    # (ADR 0017); the client hides "Describe it in your words" while it is off (RS-106).
    process_drafts_enabled: bool = False


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    if not settings.anthropic_model:
        settings.anthropic_model = DEFAULT_ANTHROPIC_MODEL
    return settings
