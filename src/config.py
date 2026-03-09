"""Application settings loaded from environment variables and .env files."""

import sys
from typing import Any

from pydantic import ValidationError, field_validator
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
    podcast_email: str = ""
    podcast_cover_url: str = ""
    base_url: str
    episodes_dir: str = "episodes"
    vault_output_dir: str
    crossfade_ms: int = 30
    target_dbfs: float = -20.0

    # Phase 4: Web Dashboard
    dashboard_username: str = "admin"
    REDACTED_FIELD_hash: str
    dashboard_host: str = "127.0.0.1"

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

    @field_validator("REDACTED_FIELD_hash")
    @classmethod
    def _must_be_argon2id(cls, v: str) -> str:
        if not v.startswith("$argon2id$"):
            raise ValueError(
                "not a valid Argon2id hash (run: python -m src.hash_password)"
            )
        return v


def load_settings(**kwargs: Any) -> Settings:
    """Load and validate settings, printing a friendly error checklist on failure.

    Accepts the same keyword arguments as Settings() (e.g. _env_file for testing).
    """
    try:
        return Settings(**kwargs)
    except ValidationError as e:
        print("\nConfiguration errors found:\n")
        for err in e.errors():
            field_name = str(err["loc"][0])
            env_var = field_name.upper()
            msg = err["msg"]
            print(f"  \u2717 {env_var} \u2014 {msg}")
        print("\nFix these in your .env file and try again.")
        sys.exit(1)
