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
