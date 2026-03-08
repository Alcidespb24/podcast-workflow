class PodcastError(Exception):
    """Base exception for all podcast workflow errors."""


class ConfigurationError(PodcastError):
    """Required configuration (e.g. API key) is missing or invalid."""


class InputError(PodcastError):
    """Input files are missing, unreadable, or empty."""


class ScriptGenerationError(PodcastError):
    """Script generation LLM call failed or returned empty content."""


class TTSError(PodcastError):
    """TTS API call failed or returned an unexpected response."""


class AudioWriteError(PodcastError):
    """Output audio file could not be written."""


class EncodingError(PodcastError):
    """MP3 encoding or audio processing failure."""


class RSSError(PodcastError):
    """RSS feed generation or validation failure."""


class RateLimitError(PodcastError):
    """API returned 429 rate-limit response."""

    def __init__(self, message: str, retry_after: float | None = None) -> None:
        super().__init__(message)
        self.retry_after = retry_after
