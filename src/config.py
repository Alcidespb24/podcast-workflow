"""Application settings loaded from environment variables and .env files."""

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central configuration sourced from environment / .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    google_api_key: str
    database_url: str = "sqlite:///data/podcast.db"

    default_host_a_name: str = "Joe"
    default_host_a_voice: str = "Kore"
    default_host_b_name: str = "Jane"
    default_host_b_voice: str = "Puck"
    default_style_tone: str = "Informative & engaging"

    # Phase 2: Audio processing and distribution
    podcast_name: str = "My Knowledge Podcast"
    base_url: str
    episodes_dir: str = "episodes"
    vault_output_dir: str
    crossfade_ms: int = 30
    target_dbfs: float = -20.0

    # Phase 3: Automation
    watcher_enabled: bool = True
    watcher_debounce_seconds: float = 1.5
    job_cooldown_seconds: float = 10.0
    job_poll_interval_seconds: float = 5.0
    max_retries: int = 3
    backoff_initial_seconds: float = 5.0
    backoff_multiplier: float = 2.0
    backoff_max_seconds: float = 300.0

    @field_validator("base_url")
    @classmethod
    def _base_url_must_be_https(cls, v: str) -> str:
        if not v.startswith("https://"):
            raise ValueError("base_url must start with https://")
        return v.rstrip("/")
