"""Google Gemini TTS client with dynamic multi-speaker voice configuration."""

from google import genai
from google.genai import types
from google.genai.errors import APIError

from src.domain.models import Host
from src.exceptions import RateLimitError, TTSError


class GoogleTTSClient:
    """Synthesizes podcast audio from script text using Gemini TTS."""

    def __init__(self, api_key: str) -> None:
        self._client = genai.Client(api_key=api_key)

    def synthesize(self, script: str, hosts: list[Host]) -> bytes:
        """Convert a script chunk to PCM audio bytes.

        Builds a MultiSpeakerVoiceConfig dynamically from the provided hosts
        so no speaker names are hardcoded.

        Args:
            script: Podcast script text with speaker labels.
            hosts: Host objects defining speaker names and TTS voices.

        Returns:
            Raw PCM audio bytes.

        Raises:
            RateLimitError: If the API returns a 429 rate-limit response.
            TTSError: If the API call fails or returns no audio data.
        """
        host_names = " and ".join(h.name for h in hosts)
        tts_prompt = f"TTS the following conversation between {host_names}:\n{script}"

        speaker_configs = [
            types.SpeakerVoiceConfig(
                speaker=host.name,
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(
                        voice_name=host.voice
                    )
                ),
            )
            for host in hosts
        ]

        try:
            response = self._client.models.generate_content(
                model="gemini-2.5-flash-preview-tts",
                contents=tts_prompt,
                config=types.GenerateContentConfig(
                    response_modalities=["AUDIO"],
                    speech_config=types.SpeechConfig(
                        multi_speaker_voice_config=types.MultiSpeakerVoiceConfig(
                            speaker_voice_configs=speaker_configs
                        )
                    ),
                ),
            )
        except APIError as e:
            if getattr(e, "code", None) == 429:
                raise RateLimitError(f"TTS rate-limited: {e}") from e
            raise TTSError(f"TTS API request failed: {e}") from e
        except Exception as e:
            raise TTSError(f"TTS API request failed: {e}") from e

        if not response.candidates:
            raise TTSError("TTS API returned no candidates.")

        candidate = response.candidates[0]
        content = candidate.content
        finish_reason = getattr(candidate, "finish_reason", None)

        if not content or not getattr(content, "parts", None):
            raise TTSError(
                f"TTS API returned empty audio (finish_reason={finish_reason!r}). "
                "The input may be too long -- try splitting it into smaller files."
            )

        part = content.parts[0]
        inline_data = getattr(part, "inline_data", None)
        if not inline_data or not inline_data.data:
            raise TTSError(
                f"TTS response contains no audio data (finish_reason={finish_reason!r})."
            )

        return inline_data.data


