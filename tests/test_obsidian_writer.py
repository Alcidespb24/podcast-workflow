"""Tests for Obsidian vault writer -- MP3 copy and episode note creation."""

from datetime import datetime, timezone
from pathlib import Path

import pytest
import yaml

from src.domain.models import Episode
from src.infrastructure.obsidian_writer import write_episode_to_vault


@pytest.fixture()
def episode() -> Episode:
    """Return a sample episode for vault writing tests."""
    return Episode(
        title="Test Episode",
        description="A test episode description",
        episode_number=1,
        filename="2026-03-08_test-episode.mp3",
        duration_seconds=125.5,
        file_size=2_000_000,
        hosts=["Joe", "Jane"],
        style_name="Default",
        source_file="notes/test.md",
        published_at=datetime(2026, 3, 8, 12, 0, 0, tzinfo=timezone.utc),
    )


@pytest.fixture()
def mp3_source(tmp_path: Path) -> Path:
    """Create a dummy MP3 source file."""
    source = tmp_path / "source" / "episode.mp3"
    source.parent.mkdir(parents=True)
    source.write_bytes(b"\xff\xfb\x90\x00" * 256)  # fake MP3 data
    return source


@pytest.fixture()
def vault_dir(tmp_path: Path) -> Path:
    """Return a path for the vault output directory (not yet created)."""
    return tmp_path / "vault_output"


def test_mp3_saved(
    episode: Episode, mp3_source: Path, vault_dir: Path
) -> None:
    """MP3 file is copied to vault_output_dir with correct filename."""
    mp3_path, _ = write_episode_to_vault(
        episode, str(mp3_source), "Transcript text.", str(vault_dir)
    )
    assert Path(mp3_path).exists()
    assert Path(mp3_path).stat().st_size == mp3_source.stat().st_size


def test_mp3_saved_creates_dir(
    episode: Episode, mp3_source: Path, vault_dir: Path
) -> None:
    """vault_output_dir is created if it doesn't exist."""
    assert not vault_dir.exists()
    write_episode_to_vault(
        episode, str(mp3_source), "Transcript text.", str(vault_dir)
    )
    assert vault_dir.exists()


def test_episode_note_created(
    episode: Episode, mp3_source: Path, vault_dir: Path
) -> None:
    """Markdown note file created at vault_output_dir/{date} - {title}.md."""
    _, note_path = write_episode_to_vault(
        episode, str(mp3_source), "Transcript text.", str(vault_dir)
    )
    assert Path(note_path).exists()
    assert note_path.endswith(".md")
    assert "2026-03-08" in note_path
    assert "Test Episode" in note_path


def test_note_frontmatter(
    episode: Episode, mp3_source: Path, vault_dir: Path
) -> None:
    """Note contains YAML frontmatter with required fields."""
    _, note_path = write_episode_to_vault(
        episode, str(mp3_source), "Transcript text.", str(vault_dir)
    )
    content = Path(note_path).read_text(encoding="utf-8")

    # Extract YAML frontmatter between --- markers
    parts = content.split("---")
    assert len(parts) >= 3, "Note must have YAML frontmatter between --- markers"
    frontmatter = yaml.safe_load(parts[1])

    assert frontmatter["title"] == "Test Episode"
    assert frontmatter["date"] == "2026-03-08"
    assert frontmatter["episode_number"] == 1
    assert frontmatter["hosts"] == ["Joe", "Jane"]
    assert frontmatter["style"] == "Default"
    assert frontmatter["source_file"] == "notes/test.md"
    assert frontmatter["duration"] == "2:05"
    assert "podcast" in frontmatter["tags"]
    assert "episode" in frontmatter["tags"]


def test_note_audio_link(
    episode: Episode, mp3_source: Path, vault_dir: Path
) -> None:
    """Note contains Obsidian wiki link for audio embed."""
    _, note_path = write_episode_to_vault(
        episode, str(mp3_source), "Transcript text.", str(vault_dir)
    )
    content = Path(note_path).read_text(encoding="utf-8")
    assert "![[2026-03-08 - Test Episode.mp3]]" in content


def test_note_transcript_callout(
    episode: Episode, mp3_source: Path, vault_dir: Path
) -> None:
    """Note contains foldable callout with transcript lines prefixed by '> '."""
    transcript = "Line one of transcript.\nLine two of transcript."
    _, note_path = write_episode_to_vault(
        episode, str(mp3_source), transcript, str(vault_dir)
    )
    content = Path(note_path).read_text(encoding="utf-8")
    assert "> [!note]- Transcript" in content
    assert "> Line one of transcript." in content
    assert "> Line two of transcript." in content


def test_filename_sanitized(
    mp3_source: Path, vault_dir: Path
) -> None:
    """Titles with special chars produce safe filenames."""
    episode = Episode(
        title='Bad: Title / With "Special" Chars?',
        description="Test",
        episode_number=2,
        filename="2026-03-08_bad-title.mp3",
        duration_seconds=60.0,
        file_size=1_000_000,
        hosts=["Joe"],
        style_name="Default",
        source_file="notes/bad.md",
        published_at=datetime(2026, 3, 8, 12, 0, 0, tzinfo=timezone.utc),
    )
    mp3_path, note_path = write_episode_to_vault(
        episode, str(mp3_source), "Transcript.", str(vault_dir)
    )
    # Filenames should exist and not contain illegal chars
    assert Path(mp3_path).exists()
    assert Path(note_path).exists()
    mp3_name = Path(mp3_path).name
    note_name = Path(note_path).name
    for char in ['<', '>', ':', '"', '/', '\\', '|', '?', '*']:
        assert char not in mp3_name, f"Illegal char {char!r} in MP3 filename"
        assert char not in note_name, f"Illegal char {char!r} in note filename"
