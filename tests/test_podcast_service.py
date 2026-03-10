"""Tests for the podcast pipeline service."""

from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from argon2 import PasswordHasher
from pydub import AudioSegment
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from src.application.podcast_service import (
    _extract_description,
    _extract_title,
    generate_podcast,
)
from src.config import Settings
from src.domain.models import Episode, Host, PipelineConfig, Style
from src.infrastructure.database.models import Base

_ph = PasswordHasher()
TEST_HASH = _ph.hash("testpass")


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
def settings(tmp_path: Path) -> Settings:
    return Settings(
        google_api_key="test-key",
        database_url="sqlite:///:memory:",
        base_url="https://example.com",
        vault_output_dir=str(tmp_path / "vault"),
        episodes_dir=str(tmp_path / "episodes"),
        REDACTED_FIELD_hash=TEST_HASH,
        session_secret_key="test-secret-key-for-testing",
    )


@pytest.fixture()
def db_session() -> Session:
    """Create an in-memory SQLite session with all tables."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


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
        # Return 100 bytes of valid PCM (16-bit mono, even byte count)
        instance.synthesize.return_value = b"\x00" * 100
        cls.return_value = instance
        yield instance


@pytest.fixture()
def mock_process_audio():
    with patch("src.application.podcast_service.process_audio") as mock:
        # Return a short AudioSegment (1 second of silence)
        seg = AudioSegment.silent(duration=1000, frame_rate=24000)
        mock.return_value = seg
        yield mock


@pytest.fixture()
def mock_export_mp3():
    with patch("src.application.podcast_service.export_tagged_mp3") as mock:
        yield mock


@pytest.fixture()
def mock_build_feed():
    with patch("src.application.podcast_service.build_podcast_feed") as mock:
        mock.return_value = "<rss><channel></channel></rss>"
        yield mock


@pytest.fixture()
def mock_validate_rss():
    with patch("src.application.podcast_service.validate_podcast_rss") as mock:
        mock.return_value = []
        yield mock


@pytest.fixture()
def mock_write_vault():
    with patch("src.application.podcast_service.write_episode_to_vault") as mock:
        mock.return_value = ("/vault/ep.mp3", "/vault/ep.md")
        yield mock


@pytest.fixture()
def mock_file_size():
    with patch("src.application.podcast_service.os.path.getsize") as mock:
        mock.return_value = 12345
        yield mock


@pytest.fixture()
def all_mocks(
    mock_script_gen,
    mock_tts,
    mock_process_audio,
    mock_export_mp3,
    mock_build_feed,
    mock_validate_rss,
    mock_write_vault,
    mock_file_size,
):
    """Bundle all mocks together for integration tests."""
    return {
        "script_gen": mock_script_gen,
        "tts": mock_tts,
        "process_audio": mock_process_audio,
        "export_mp3": mock_export_mp3,
        "build_feed": mock_build_feed,
        "validate_rss": mock_validate_rss,
        "write_vault": mock_write_vault,
        "file_size": mock_file_size,
    }


# ---------------------------------------------------------------------------
# Unit tests for helper functions
# ---------------------------------------------------------------------------


class TestExtractTitle:
    def test_extracts_h1_heading(self) -> None:
        content = "# My Great Episode\nSome body text."
        assert _extract_title(content, "fallback.md") == "My Great Episode"

    def test_extracts_first_h1_only(self) -> None:
        content = "Intro text\n# First Heading\n# Second Heading"
        assert _extract_title(content, "fallback.md") == "First Heading"

    def test_falls_back_to_filename_stem(self) -> None:
        content = "No headings here, just text."
        assert _extract_title(content, "my-episode.md") == "my-episode"

    def test_strips_whitespace_from_title(self) -> None:
        content = "#   Spaced Title   \nContent"
        assert _extract_title(content, "f.md") == "Spaced Title"


class TestExtractDescription:
    def test_short_content_returned_as_is(self) -> None:
        assert _extract_description("Short text.") == "Short text."

    def test_long_content_truncated_at_word_boundary(self) -> None:
        text = "word " * 50  # 250 chars
        desc = _extract_description(text, max_length=200)
        assert len(desc) <= 200
        assert not desc.endswith(" ")

    def test_exact_length_not_truncated(self) -> None:
        text = "x" * 200
        assert _extract_description(text, max_length=200) == text


# ---------------------------------------------------------------------------
# Integration tests for generate_podcast()
# ---------------------------------------------------------------------------


class TestPipelineReturnsEpisode:
    def test_returns_episode_domain_model(
        self, config, settings, db_session, all_mocks
    ) -> None:
        result = generate_podcast(config, settings, db_session)
        assert isinstance(result, Episode)
        assert result.title == "Test Episode"
        assert result.episode_number == 1
        assert result.id is not None


class TestPipelineCallsAudioProcessing:
    def test_calls_process_audio_with_tts_output(
        self, config, settings, db_session, all_mocks
    ) -> None:
        generate_podcast(config, settings, db_session)
        all_mocks["process_audio"].assert_called_once()
        # Should pass the TTS bytes and settings
        call_kwargs = all_mocks["process_audio"].call_args
        assert call_kwargs.kwargs["crossfade_ms"] == settings.crossfade_ms
        assert call_kwargs.kwargs["target_dbfs"] == settings.target_dbfs


class TestPipelineCallsExportMp3:
    def test_calls_export_tagged_mp3(
        self, config, settings, db_session, all_mocks
    ) -> None:
        generate_podcast(config, settings, db_session)
        all_mocks["export_mp3"].assert_called_once()
        call_kwargs = all_mocks["export_mp3"].call_args
        assert call_kwargs.kwargs["title"] == "Test Episode"
        assert call_kwargs.kwargs["artist"] == settings.podcast_name
        assert call_kwargs.kwargs["track_number"] == 1


class TestPipelinePersistsEpisode:
    def test_episode_persisted_in_database(
        self, config, settings, db_session, all_mocks
    ) -> None:
        from src.infrastructure.database.repositories import EpisodeRepository

        episode = generate_podcast(config, settings, db_session)
        repo = EpisodeRepository(db_session)
        all_eps = repo.get_all()
        assert len(all_eps) == 1
        assert all_eps[0].title == "Test Episode"
        assert all_eps[0].id == episode.id


class TestPipelineRegeneratesRSS:
    def test_calls_build_podcast_feed(
        self, config, settings, db_session, all_mocks
    ) -> None:
        generate_podcast(config, settings, db_session)
        all_mocks["build_feed"].assert_called_once()
        call_args = all_mocks["build_feed"].call_args[0]
        assert call_args[0] == settings.podcast_name
        assert call_args[2] == settings.base_url

    def test_writes_feed_xml_to_episodes_dir(
        self, config, settings, db_session, all_mocks
    ) -> None:
        generate_podcast(config, settings, db_session)
        feed_path = Path(settings.episodes_dir) / "feed.xml"
        assert feed_path.exists()


class TestPipelineWritesToVault:
    def test_calls_write_episode_to_vault(
        self, config, settings, db_session, all_mocks
    ) -> None:
        generate_podcast(config, settings, db_session)
        all_mocks["write_vault"].assert_called_once()
        call_args = all_mocks["write_vault"].call_args[0]
        # First arg is Episode, second is export path, third is script, fourth is vault dir
        assert isinstance(call_args[0], Episode)
        assert call_args[3] == settings.vault_output_dir


class TestPipelineCallsScriptGenOnce:
    def test_pipeline_calls_script_gen_once(
        self, config, settings, db_session, all_mocks
    ) -> None:
        generate_podcast(config, settings, db_session)
        all_mocks["script_gen"].generate.assert_called_once()


class TestPipelineCallsTtsPerChunk:
    def test_pipeline_calls_tts_per_chunk(
        self, config, settings, db_session, all_mocks
    ) -> None:
        # Script with two chunks (long enough to split)
        turn_a = "Joe: " + "A" * 7000
        turn_b = "Jane: " + "B" * 7000
        all_mocks["script_gen"].generate.return_value = f"{turn_a}\n{turn_b}"
        generate_podcast(config, settings, db_session)
        assert all_mocks["tts"].synthesize.call_count == 2


class TestPipelineValidatesSpeakers:
    def test_pipeline_validates_speakers(
        self, config, settings, db_session, all_mocks
    ) -> None:
        all_mocks["script_gen"].generate.return_value = (
            "Joe: Hello\nBob: Unexpected speaker"
        )
        # Should still complete (log warning, continue anyway)
        generate_podcast(config, settings, db_session)
        assert all_mocks["tts"].synthesize.called


class TestPipelineNormalizesSpeakers:
    def test_pipeline_normalizes_speakers(
        self, config, settings, db_session, all_mocks
    ) -> None:
        all_mocks["script_gen"].generate.return_value = "joe: Hello\njane: Hi there"
        generate_podcast(config, settings, db_session)
        # TTS should receive normalized script
        call_args = all_mocks["tts"].synthesize.call_args
        script_arg = call_args[0][0]
        assert "Joe:" in script_arg
        assert "Jane:" in script_arg


class TestPipelineSanitizesBeforeScriptGen:
    def test_pipeline_sanitizes_before_script_gen(
        self, hosts, style, settings, tmp_path, db_session, all_mocks
    ) -> None:
        md_file = tmp_path / "raw.md"
        md_file.write_text("# Title\n```python\ncode block\n```\nActual content")
        cfg = PipelineConfig(hosts=hosts, style=style, source_file=str(md_file))
        generate_podcast(cfg, settings, db_session)
        prompt_arg = all_mocks["script_gen"].generate.call_args[0][0]
        assert "```" not in prompt_arg
        assert "Actual content" in prompt_arg


class TestPipelineEpisodeNumberAutoIncrements:
    def test_second_episode_gets_number_two(
        self, config, settings, db_session, all_mocks
    ) -> None:
        ep1 = generate_podcast(config, settings, db_session)
        assert ep1.episode_number == 1

        ep2 = generate_podcast(config, settings, db_session)
        assert ep2.episode_number == 2


class TestPipelineRSSErrorNonFatal:
    def test_rss_error_does_not_fail_pipeline(
        self, config, settings, db_session, all_mocks
    ) -> None:
        from src.exceptions import RSSError

        all_mocks["build_feed"].side_effect = RSSError("Feed generation failed")
        # Should still return episode successfully
        result = generate_podcast(config, settings, db_session)
        assert isinstance(result, Episode)
