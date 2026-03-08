"""Domain models for the podcast workflow pipeline."""

from pydantic import BaseModel, Field, field_validator


class Host(BaseModel):
    """A podcast host with a name, TTS voice identifier, and role."""

    id: int | None = None
    name: str
    voice: str
    role: str = "host"


class Style(BaseModel):
    """Podcast style configuration controlling tone and delivery."""

    id: int | None = None
    name: str
    tone: str
    personality_guidance: str | None = None
    speaker_count: int = Field(default=2, ge=2, le=2)


class PipelineConfig(BaseModel):
    """Full configuration for a single pipeline run."""

    hosts: list[Host]
    style: Style
    source_file: str

    @field_validator("hosts")
    @classmethod
    def _require_exactly_two_hosts(cls, v: list[Host]) -> list[Host]:
        if len(v) != 2:
            raise ValueError("Exactly 2 hosts required")
        return v
