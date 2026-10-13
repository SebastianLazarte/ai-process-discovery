from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

DEFAULT_ANTHROPIC_MODEL = "claude-opus-5"
DEFAULT_WEB_DIR = Path(__file__).resolve().parents[3] / "web"


class Settings(BaseSettings):
    """Runtime configuration. Every value comes from the environment or a local .env file."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "sqlite:///./apd.sqlite"

    llm_provider: Literal["fake", "anthropic"] = "fake"
    anthropic_api_key: SecretStr | None = None
    anthropic_model: str = DEFAULT_ANTHROPIC_MODEL
    llm_timeout_seconds: float = 60.0
    llm_max_retries: int = 2

    log_level: str = "INFO"

    # Public deployment (ADR 0008): the web client warns that data is public and short-lived.
    public_demo: bool = False

    web_dir: Path = DEFAULT_WEB_DIR


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    if not settings.anthropic_model:
        settings.anthropic_model = DEFAULT_ANTHROPIC_MODEL
    return settings
