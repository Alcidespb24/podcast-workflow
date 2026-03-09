"""Audio post-processing: crossfade, RMS normalisation, MP3 export, ID3 tagging.

Also retains the legacy ``write_wav`` helper for backward compatibility.
"""

from __future__ import annotations

import wave

from pydub import AudioSegment

from src.exceptions import AudioWriteError, EncodingError

# ---------------------------------------------------------------------------
# Ensure pydub can locate ffmpeg even when it is not on PATH.
# The imageio-ffmpeg package bundles a static build we can fall back to.
# ---------------------------------------------------------------------------

def _configure_ffmpeg() -> None:
    """Point pydub at ffmpeg, searching common install locations as fallback."""
    import os
    from pathlib import Path
    from pydub.utils import which as _which

    if _which("ffmpeg") is not None:
        return  # system ffmpeg is fine

    # Check common Windows install locations
    candidates = [
        Path(os.environ.get("LOCALAPPDATA", "")) / "Microsoft/WinGet/Links/ffmpeg.exe",
        Path(os.environ.get("ProgramFiles", "")) / "ffmpeg/bin/ffmpeg.exe",
    ]
    for path in candidates:
        if path.is_file():
            AudioSegment.converter = str(path)
            return

    try:
        import imageio_ffmpeg
        AudioSegment.converter = imageio_ffmpeg.get_ffmpeg_exe()
    except ImportError:
        pass  # let pydub raise its own error later if needed


_configure_ffmpeg()


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def rms_normalize(seg: AudioSegment, target_dbfs: float = -20.0) -> AudioSegment:
    """Normalise *seg* so its RMS level matches *target_dbfs*.

    Silent (all-zero) segments are returned unchanged to avoid division by
    zero inside ``dBFS``.
    """
    if seg.rms == 0:
        return seg
    gain = target_dbfs - seg.dBFS
    return seg.apply_gain(gain)


def process_audio(
    pcm_chunks: list[bytes],
    *,
    sample_width: int = 2,
    frame_rate: int = 24000,
    channels: int = 1,
    crossfade_ms: int = 30,
    target_dbfs: float = -20.0,
) -> AudioSegment:
    """Convert raw PCM chunks into a single crossfaded, RMS-normalised segment.

    Parameters
    ----------
    pcm_chunks:
        List of raw PCM byte strings (e.g. from Gemini TTS).
    sample_width:
        Bytes per sample (default 2 = 16-bit).
    frame_rate:
        Samples per second (default 24 000).
    channels:
        Number of audio channels (default 1 = mono).
    crossfade_ms:
        Overlap duration in milliseconds applied between adjacent chunks.
        Automatically clamped to the shorter of the two segments being joined.
    target_dbfs:
        RMS normalisation target in dBFS.

    Returns
    -------
    AudioSegment
        The combined, normalised audio ready for export.
    """
    segments: list[AudioSegment] = []
    for chunk in pcm_chunks:
        seg = AudioSegment(
            data=chunk,
            sample_width=sample_width,
            frame_rate=frame_rate,
            channels=channels,
        )
        seg = rms_normalize(seg, target_dbfs)
        segments.append(seg)

    if len(segments) == 1:
        return segments[0]

    combined = segments[0]
    for seg in segments[1:]:
        # Clamp crossfade to the shorter of the two segments to avoid ValueError
        fade = min(crossfade_ms, len(combined), len(seg))
        combined = combined.append(seg, crossfade=fade)

    return combined


def export_tagged_mp3(
    audio: AudioSegment,
    output_path: str,
    *,
    title: str,
    artist: str,
    track_number: int,
) -> None:
    """Export *audio* as CBR 128 kbps mono MP3 with ID3 tags.

    Raises
    ------
    EncodingError
        If the MP3 export or tagging step fails (bad path, ffmpeg error, etc.).
    """
    try:
        audio.export(
            output_path,
            format="mp3",
            bitrate="128k",
            parameters=["-ac", "1"],
        )
    except Exception as exc:
        raise EncodingError(
            f"MP3 export failed for '{output_path}': {exc}"
        ) from exc

    # Apply ID3 tags with mutagen ------------------------------------------------
    try:
        from mutagen.easyid3 import EasyID3
        from mutagen.id3 import ID3NoHeaderError

        try:
            tags = EasyID3(output_path)
        except ID3NoHeaderError:
            from mutagen.id3 import ID3

            ID3().save(output_path)
            tags = EasyID3(output_path)

        tags["title"] = title
        tags["artist"] = artist
        tags["tracknumber"] = str(track_number)
        tags.save()
    except Exception as exc:
        raise EncodingError(
            f"ID3 tagging failed for '{output_path}': {exc}"
        ) from exc


# ---------------------------------------------------------------------------
# Legacy helper (backward compatibility)
# ---------------------------------------------------------------------------


def write_wav(
    filename: str,
    pcm: bytes,
    channels: int = 1,
    rate: int = 24000,
    sample_width: int = 2,
) -> None:
    """Write raw PCM bytes to a WAV file.

    Retained for backward compatibility with earlier pipeline stages.
    """
    try:
        with wave.open(filename, "wb") as wf:
            wf.setnchannels(channels)
            wf.setsampwidth(sample_width)
            wf.setframerate(rate)
            wf.writeframes(pcm)
    except OSError as exc:
        raise AudioWriteError(
            f"Could not write audio file '{filename}': {exc}"
        ) from exc
