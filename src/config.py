"""Application settings loaded from environment variables and .env files."""

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
