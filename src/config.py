"""Application settings loaded from environment variables and .env files."""

import sys
from pathlib import Path
from typing import Any

from pydantic import ValidationError, field_validator, model_validator
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
    dashboard_password_hash: str
    dashboard_host: str = "127.0.0.1"

    # Phase 6: Session authentication
    session_secret_key: str
    session_timeout_hours: float = 168

    # Phase 7: HTTP hardening
    cors_allowed_origins: str = ""

    # Phase 8: Path validation
    vault_base_dir: str

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

    @field_validator("dashboard_password_hash")
    @classmethod
    def _must_be_argon2id(cls, v: str) -> str:
        if not v.startswith("$argon2id$"):
            raise ValueError(
                "not a valid Argon2id hash (run: python -m src.hash_password)"
            )
        return v

    @field_validator("vault_base_dir")
    @classmethod
    def _resolve_vault_base_dir(cls, v: str) -> str:
        resolved = Path(v).resolve(strict=False)
        if not resolved.is_dir():
            raise ValueError(f"directory does not exist: {v}")
        return str(resolved)

    @model_validator(mode="after")
    def _vault_output_within_base(self) -> "Settings":
        output = Path(self.vault_output_dir).resolve(strict=False)
        base = Path(self.vault_base_dir)  # Already resolved by field_validator
        if not output.is_relative_to(base):
            raise ValueError("VAULT_OUTPUT_DIR must be within VAULT_BASE_DIR")
        return self


def load_settings(**kwargs: Any) -> Settings:
    """Load and validate settings, printing a friendly error checklist on failure.

    Accepts the same keyword arguments as Settings() (e.g. _env_file for testing).
    """
    try:
        return Settings(**kwargs)
    except ValidationError as e:
        print("\nConfiguration errors found:\n")
        for err in e.errors():
            if err["loc"]:
                field_name = str(err["loc"][0])
                env_var = field_name.upper()
                print(f"  \u2717 {env_var} \u2014 {err['msg']}")
            else:
                print(f"  \u2717 {err['msg']}")
        print("\nFix these in your .env file and try again.")
        sys.exit(1)
