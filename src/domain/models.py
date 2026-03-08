"""Domain models for the podcast workflow pipeline."""

import re
from datetime import datetime

from pydantic import BaseModel, Field, field_validator

_ILLEGAL_FILENAME_CHARS = re.compile(r'[<>:"/\\|?*]')
_TRAILING_DOTS_SPACES = re.compile(r'[. ]+$')


def sanitize_filename(name: str, max_length: int = 200) -> str:
    """Strip illegal filesystem characters, trailing dots/spaces, and limit length."""
    cleaned = _ILLEGAL_FILENAME_CHARS.sub("", name)
    cleaned = cleaned[:max_length]
    cleaned = _TRAILING_DOTS_SPACES.sub("", cleaned)
    return cleaned


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


class Episode(BaseModel):
    """A single podcast episode with metadata."""

    id: int | None = None
    title: str
    description: str
    episode_number: int
    filename: str
    duration_seconds: float
    file_size: int
    hosts: list[str]
    style_name: str
    source_file: str
    published_at: datetime

    @property
    def duration_str(self) -> str:
        """Format duration_seconds as 'MM:SS' or 'H:MM:SS'."""
        total = int(self.duration_seconds)
        hours, remainder = divmod(total, 3600)
        minutes, seconds = divmod(remainder, 60)
        if hours > 0:
            return f"{hours}:{minutes:02d}:{seconds:02d}"
        return f"{minutes}:{seconds:02d}"
