"""Domain models for the podcast workflow pipeline."""

import enum
import re
from datetime import datetime

from pydantic import BaseModel, Field, field_validator

_ILLEGAL_FILENAME_CHARS = re.compile(r'[<>:"/\\|?*]')
_TRAILING_DOTS_SPACES = re.compile(r"[. ]+$")
_NON_ALNUM = re.compile(r"[^a-z0-9]+")
_LEADING_TRAILING_HYPHENS = re.compile(r"^-+|-+$")


def sanitize_filename(name: str, max_length: int = 200) -> str:
    """Strip illegal filesystem characters, trailing dots/spaces, and limit length."""
    cleaned = _ILLEGAL_FILENAME_CHARS.sub("", name)
    cleaned = cleaned[:max_length]
    cleaned = _TRAILING_DOTS_SPACES.sub("", cleaned)
    return cleaned


def slugify_filename(name: str, max_length: int = 200) -> str:
    """Convert a title into a URL-safe slug (lowercase, hyphens, no special chars)."""
    slug = _NON_ALNUM.sub("-", name.lower())
    slug = _LEADING_TRAILING_HYPHENS.sub("", slug)
    return slug[:max_length]


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
    cover_url: str = ""

    @property
    def duration_str(self) -> str:
        """Format duration_seconds as 'MM:SS' or 'H:MM:SS'."""
        total = int(self.duration_seconds)
        hours, remainder = divmod(total, 3600)
        minutes, seconds = divmod(remainder, 60)
        if hours > 0:
            return f"{hours}:{minutes:02d}:{seconds:02d}"
        return f"{minutes}:{seconds:02d}"


# ---------------------------------------------------------------------------
# Phase 3: Automation models
# ---------------------------------------------------------------------------


class JobState(str, enum.Enum):
    """Lifecycle states for an automation job."""

    PENDING = "pending"
    PROCESSING = "processing"
    ENCODING = "encoding"
    PUBLISHING = "publishing"
    COMPLETE = "complete"
    FAILED = "failed"

    def valid_transitions(self) -> set["JobState"]:
        """Return the set of states this state can transition to."""
        _MAP: dict[JobState, set[JobState]] = {
            JobState.PENDING: {JobState.PROCESSING, JobState.FAILED},
            JobState.PROCESSING: {JobState.ENCODING, JobState.FAILED},
            JobState.ENCODING: {JobState.PUBLISHING, JobState.FAILED},
            JobState.PUBLISHING: {JobState.COMPLETE, JobState.FAILED},
            JobState.COMPLETE: set(),
            JobState.FAILED: set(),
        }
        return _MAP[self]


class Preset(BaseModel):
    """Maps a vault folder to a host pair, style, and optional personality override."""

    id: int | None = None
    folder_path: str
    host_a_id: int
    host_b_id: int
    style_id: int
    personality_guidance: str | None = None


class Job(BaseModel):
    """A queued pipeline execution tied to a preset."""

    id: int | None = None
    source_file: str
    preset_id: int
    state: JobState = JobState.PENDING
    error_message: str | None = None
    retry_count: int = 0
    created_at: datetime | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
