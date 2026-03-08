"""Tests for RSS feed generation and validation."""

from datetime import datetime, timezone

import pytest

from src.domain.models import Episode
from src.infrastructure.rss import build_podcast_feed, validate_podcast_rss


@pytest.fixture()
def base_url() -> str:
    return "https://podcast.example.com"


@pytest.fixture()
def episodes() -> list[Episode]:
    return [
        Episode(
            title="First Episode",
            description="Introduction to the podcast",
            episode_number=1,
            filename="2026-03-01_first-episode.mp3",
            duration_seconds=300.0,
            file_size=4_800_000,
            hosts=["Joe", "Jane"],
            style_name="Default",
            source_file="notes/first.md",
            published_at=datetime(2026, 3, 1, 10, 0, 0, tzinfo=timezone.utc),
        ),
        Episode(
            title="Second Episode",
            description="Deep dive into Python",
            episode_number=2,
            filename="2026-03-08_second-episode.mp3",
            duration_seconds=7500.0,
            file_size=12_000_000,
            hosts=["Joe", "Jane"],
            style_name="Conversational",
            source_file="notes/second.md",
            published_at=datetime(2026, 3, 8, 14, 30, 0, tzinfo=timezone.utc),
        ),
    ]


# --- Feed generation tests ---


def test_itunes_namespace(base_url: str, episodes: list[Episode]) -> None:
    """Generated RSS XML contains iTunes namespace tags at channel level."""
    xml = build_podcast_feed("Test Podcast", "A test podcast", base_url, episodes)
    assert "itunes:author" in xml
    assert "itunes:explicit" in xml
    assert "itunes:category" in xml


def test_episode_metadata(base_url: str, episodes: list[Episode]) -> None:
    """Each RSS item has title, description, enclosure, guid, pubDate."""
    xml = build_podcast_feed("Test Podcast", "A test podcast", base_url, episodes)
    assert "<title>First Episode</title>" in xml
    assert "<title>Second Episode</title>" in xml
    assert "<description>Introduction to the podcast</description>" in xml
    assert 'type="audio/mpeg"' in xml
    assert "<guid" in xml
    assert "<pubDate>" in xml


def test_enclosure_url_uses_base_url(base_url: str, episodes: list[Episode]) -> None:
    """Enclosure URL is constructed as {base_url}/episodes/{filename}."""
    xml = build_podcast_feed("Test Podcast", "A test podcast", base_url, episodes)
    assert "https://podcast.example.com/episodes/2026-03-01_first-episode.mp3" in xml
    assert "https://podcast.example.com/episodes/2026-03-08_second-episode.mp3" in xml


def test_empty_episodes(base_url: str) -> None:
    """Feed with zero episodes still validates at channel level."""
    xml = build_podcast_feed("Test Podcast", "A test podcast", base_url, [])
    errors = validate_podcast_rss(xml)
    assert errors == []


# --- Validation tests ---


def test_feed_validation_valid(base_url: str, episodes: list[Episode]) -> None:
    """A properly constructed feed passes validation (empty error list)."""
    xml = build_podcast_feed("Test Podcast", "A test podcast", base_url, episodes)
    errors = validate_podcast_rss(xml)
    assert errors == []


def test_feed_validation_missing_channel() -> None:
    """Feed without channel element fails validation."""
    bad_xml = '<?xml version="1.0" encoding="UTF-8"?><rss version="2.0"></rss>'
    errors = validate_podcast_rss(bad_xml)
    assert any("channel" in e.lower() for e in errors)


def test_feed_validation_missing_itunes() -> None:
    """Feed without required iTunes tags reports each missing tag."""
    minimal_xml = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<rss version="2.0" xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd">'
        "<channel><title>Test</title></channel></rss>"
    )
    errors = validate_podcast_rss(minimal_xml)
    assert len(errors) >= 3  # author, explicit, category
    error_text = " ".join(errors).lower()
    assert "author" in error_text
    assert "explicit" in error_text
    assert "category" in error_text
