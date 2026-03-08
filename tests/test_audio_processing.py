"""Tests for audio post-processing pipeline: crossfade, normalize, MP3 export, ID3 tags."""

import math
import struct
import tempfile
from pathlib import Path

import pytest
from pydub import AudioSegment
from pydub.utils import which as pydub_which

from src.exceptions import EncodingError
from src.infrastructure.audio import (
    export_tagged_mp3,
    process_audio,
    rms_normalize,
    write_wav,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_HAS_FFMPEG = pydub_which("ffmpeg") is not None

requires_ffmpeg = pytest.mark.skipif(
    not _HAS_FFMPEG,
    reason="ffmpeg not on PATH — MP3 tests skipped",
)


def _sine_pcm(
    freq: float = 440.0,
    duration_ms: int = 1000,
    sample_rate: int = 24000,
    amplitude: float = 0.5,
) -> bytes:
    """Generate raw 16-bit mono PCM sine wave bytes."""
    num_samples = int(sample_rate * duration_ms / 1000)
    samples = []
    for i in range(num_samples):
        t = i / sample_rate
        value = int(amplitude * 32767 * math.sin(2 * math.pi * freq * t))
        samples.append(struct.pack("<h", max(-32768, min(32767, value))))
    return b"".join(samples)


def _silent_pcm(duration_ms: int = 1000, sample_rate: int = 24000) -> bytes:
    """Generate raw 16-bit mono silent (all-zero) PCM bytes."""
    num_samples = int(sample_rate * duration_ms / 1000)
    return b"\x00\x00" * num_samples


# ---------------------------------------------------------------------------
# rms_normalize
# ---------------------------------------------------------------------------


class TestRmsNormalize:
    """Tests for rms_normalize()."""

    def test_rms_normalize(self) -> None:
        """A segment at ~-30 dBFS normalized to -20 dBFS has dBFS within +/-1 of target."""
        # Create a quiet sine wave segment
        pcm = _sine_pcm(amplitude=0.03)  # roughly -30 dBFS
        seg = AudioSegment(
            data=pcm, sample_width=2, frame_rate=24000, channels=1
        )
        assert seg.dBFS < -25, f"Precondition: source should be quiet, got {seg.dBFS}"

        result = rms_normalize(seg, target_dbfs=-20.0)

        assert abs(result.dBFS - (-20.0)) < 1.0, (
            f"Expected dBFS near -20, got {result.dBFS}"
        )

    def test_rms_normalize_silence(self) -> None:
        """A silent (all-zero) segment returns unchanged without error."""
        pcm = _silent_pcm()
        seg = AudioSegment(
            data=pcm, sample_width=2, frame_rate=24000, channels=1
        )

        result = rms_normalize(seg, target_dbfs=-20.0)

        # Should return the same segment without raising
        assert result.rms == 0
        assert len(result) == len(seg)


# ---------------------------------------------------------------------------
# process_audio (crossfade)
# ---------------------------------------------------------------------------


class TestProcessAudio:
    """Tests for process_audio() crossfade and normalization."""

    def test_crossfade(self) -> None:
        """Two 1-second segments with 30ms crossfade produce audio shorter than 2s by ~30ms."""
        chunk_a = _sine_pcm(freq=440, duration_ms=1000)
        chunk_b = _sine_pcm(freq=880, duration_ms=1000)

        result = process_audio(
            [chunk_a, chunk_b],
            crossfade_ms=30,
            target_dbfs=-20.0,
        )

        expected_ms = 2000 - 30
        assert abs(len(result) - expected_ms) < 5, (
            f"Expected ~{expected_ms}ms, got {len(result)}ms"
        )

    def test_crossfade_clamp(self) -> None:
        """Crossfade duration clamped when segment shorter than requested crossfade (no ValueError)."""
        short_pcm = _sine_pcm(duration_ms=20)  # 20ms segment
        long_pcm = _sine_pcm(duration_ms=1000)

        # Should not raise ValueError even though crossfade_ms=50 > len(short_pcm)
        result = process_audio(
            [short_pcm, long_pcm],
            crossfade_ms=50,
            target_dbfs=-20.0,
        )

        assert len(result) > 0

    def test_crossfade_single_chunk(self) -> None:
        """Single chunk returns that chunk without crossfading."""
        pcm = _sine_pcm(duration_ms=500)

        result = process_audio(
            [pcm],
            crossfade_ms=30,
            target_dbfs=-20.0,
        )

        # Single chunk -- length should be ~500ms (may differ slightly due to normalization)
        assert abs(len(result) - 500) < 5


# ---------------------------------------------------------------------------
# MP3 export and ID3 tagging
# ---------------------------------------------------------------------------


class TestMp3Export:
    """Tests for export_tagged_mp3() and MP3 output characteristics."""

    @requires_ffmpeg
    def test_mp3_export(self, tmp_path: Path) -> None:
        """process_audio exports valid MP3 file at target path, file size > 0."""
        pcm = _sine_pcm(duration_ms=2000)
        audio = process_audio([pcm], target_dbfs=-20.0)

        out = tmp_path / "test.mp3"
        export_tagged_mp3(
            audio, str(out), title="Test", artist="Bot", track_number=1
        )

        assert out.exists()
        assert out.stat().st_size > 0

    @requires_ffmpeg
    def test_id3_tags(self, tmp_path: Path) -> None:
        """export_tagged_mp3 writes title, artist, tracknumber tags readable by EasyID3."""
        from mutagen.easyid3 import EasyID3

        pcm = _sine_pcm(duration_ms=1000)
        audio = process_audio([pcm], target_dbfs=-20.0)

        out = tmp_path / "tagged.mp3"
        export_tagged_mp3(
            audio,
            str(out),
            title="My Episode",
            artist="Podcast Host",
            track_number=42,
        )

        tags = EasyID3(str(out))
        assert tags["title"] == ["My Episode"]
        assert tags["artist"] == ["Podcast Host"]
        assert tags["tracknumber"] == ["42"]

    @requires_ffmpeg
    def test_mp3_is_mono_128k(self, tmp_path: Path) -> None:
        """Exported MP3 is mono, bitrate approximately 128kbps."""
        from mutagen.mp3 import MP3

        pcm = _sine_pcm(duration_ms=2000)
        audio = process_audio([pcm], target_dbfs=-20.0)

        out = tmp_path / "mono.mp3"
        export_tagged_mp3(
            audio, str(out), title="Mono", artist="Test", track_number=1
        )

        info = MP3(str(out)).info
        assert info.channels == 1
        # CBR 128 -- allow some tolerance
        assert 120 <= info.bitrate / 1000 <= 136, (
            f"Expected ~128kbps, got {info.bitrate / 1000}kbps"
        )

    @requires_ffmpeg
    def test_encoding_error_on_bad_path(self, tmp_path: Path) -> None:
        """Export to non-existent directory raises EncodingError."""
        pcm = _sine_pcm(duration_ms=500)
        audio = process_audio([pcm], target_dbfs=-20.0)

        bad_path = str(tmp_path / "nonexistent" / "subdir" / "out.mp3")

        with pytest.raises(EncodingError):
            export_tagged_mp3(
                audio,
                bad_path,
                title="Fail",
                artist="Test",
                track_number=1,
            )


# ---------------------------------------------------------------------------
# Backward compatibility
# ---------------------------------------------------------------------------


class TestBackwardCompatibility:
    """Ensure write_wav still works."""

    def test_write_wav_still_importable(self, tmp_path: Path) -> None:
        """write_wav is still available and functional."""
        pcm = _silent_pcm(duration_ms=100)
        out = tmp_path / "compat.wav"
        write_wav(str(out), pcm)
        assert out.exists()
        assert out.stat().st_size > 0
