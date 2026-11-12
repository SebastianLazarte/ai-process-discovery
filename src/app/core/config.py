from functools import lru_cache
from typing import Annotated, Literal

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

DEFAULT_ANTHROPIC_MODEL = "claude-opus-5"
RetrievalThreshold = Annotated[float, Field(ge=-1.0, le=1.0, allow_inf_nan=False)]
# RS-119: calibrated against tests/fixtures/retrieval_gold.json. No unmeasured real-model
# default: RS-120 must evaluate a model before adding its threshold.
DEFAULT_RETRIEVAL_THRESHOLDS: dict[str, float] = {"fake-hash-256-v2": 0.35}


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
    # Per-model calibrated similarity floors. JSON in RETRIEVAL_THRESHOLDS replaces the
    # map. The old scalar setting remains an explicit operator override for migration.
    retrieval_thresholds: dict[str, RetrievalThreshold] = Field(
        default_factory=lambda: DEFAULT_RETRIEVAL_THRESHOLDS.copy()
    )
    retrieval_threshold: RetrievalThreshold | None = None

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
