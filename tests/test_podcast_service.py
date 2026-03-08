"""Tests for the podcast pipeline service."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.application.podcast_service import generate_podcast
from src.config import Settings
from src.domain.models import Host, PipelineConfig, Style


@pytest.fixture()
def hosts() -> list[Host]:
    return [
        Host(name="Joe", voice="Kore", role="host"),
        Host(name="Jane", voice="Puck", role="co-host"),
    ]


@pytest.fixture()
def style() -> Style:
    return Style(name="Default", tone="Informative & engaging")


@pytest.fixture()
def config(hosts: list[Host], style: Style, tmp_path: Path) -> PipelineConfig:
    md_file = tmp_path / "episode.md"
    md_file.write_text("# Test Episode\nSome content here.")
    return PipelineConfig(hosts=hosts, style=style, source_file=str(md_file))


@pytest.fixture()
def settings() -> Settings:
    return Settings(
        google_api_key="test-key",
        database_url="sqlite:///:memory:",
        base_url="https://example.com",
        vault_output_dir="/tmp/vault",
    )


@pytest.fixture()
def mock_script_gen():
    with patch("src.application.podcast_service.GoogleScriptGenerator") as cls:
        instance = MagicMock()
        instance.generate.return_value = "Joe: Hello\nJane: Hi there"
        cls.return_value = instance
        yield instance


@pytest.fixture()
def mock_tts():
    with patch("src.application.podcast_service.GoogleTTSClient") as cls:
        instance = MagicMock()
        instance.synthesize.return_value = b"\x00" * 100
        cls.return_value = instance
        yield instance


@pytest.fixture()
def mock_write_wav():
    with patch("src.application.podcast_service.write_wav") as mock:
        yield mock


class TestPipelineCallsScriptGenOnce:
    def test_pipeline_calls_script_gen_once(
        self, config, settings, mock_script_gen, mock_tts, mock_write_wav
    ) -> None:
        generate_podcast(config, settings)
        mock_script_gen.generate.assert_called_once()


class TestPipelineCallsTtsPerChunk:
    def test_pipeline_calls_tts_per_chunk(
        self, config, settings, mock_script_gen, mock_tts, mock_write_wav
    ) -> None:
        # Script with two chunks (long enough to split)
        turn_a = "Joe: " + "A" * 7000
        turn_b = "Jane: " + "B" * 7000
        mock_script_gen.generate.return_value = f"{turn_a}\n{turn_b}"
        generate_podcast(config, settings)
        assert mock_tts.synthesize.call_count == 2


class TestPipelineValidatesSpeakers:
    def test_pipeline_validates_speakers(
        self, config, settings, mock_script_gen, mock_tts, mock_write_wav
    ) -> None:
        mock_script_gen.generate.return_value = "Joe: Hello\nBob: Unexpected speaker"
        # Should still complete (log warning, continue anyway)
        generate_podcast(config, settings)
        assert mock_tts.synthesize.called


class TestPipelineNormalizesSpeakers:
    def test_pipeline_normalizes_speakers(
        self, config, settings, mock_script_gen, mock_tts, mock_write_wav
    ) -> None:
        mock_script_gen.generate.return_value = "joe: Hello\njane: Hi there"
        generate_podcast(config, settings)
        # TTS should receive normalized script
        call_args = mock_tts.synthesize.call_args
        script_arg = call_args[0][0]
        assert "Joe:" in script_arg
        assert "Jane:" in script_arg


class TestPipelineSanitizesBeforeScriptGen:
    def test_pipeline_sanitizes_before_script_gen(
        self, hosts, style, settings, tmp_path, mock_script_gen, mock_tts, mock_write_wav
    ) -> None:
        md_file = tmp_path / "raw.md"
        md_file.write_text("# Title\n```python\ncode block\n```\nActual content")
        cfg = PipelineConfig(hosts=hosts, style=style, source_file=str(md_file))
        generate_podcast(cfg, settings)
        prompt_arg = mock_script_gen.generate.call_args[0][0]
        assert "```" not in prompt_arg
        assert "Actual content" in prompt_arg


class TestPipelineProducesOutputFile:
    def test_pipeline_produces_output_file(
        self, config, settings, mock_script_gen, mock_tts, mock_write_wav, tmp_path
    ) -> None:
        out = str(tmp_path / "result.wav")
        result = generate_podcast(config, settings, output_file=out)
        mock_write_wav.assert_called_once()
        assert result == out
