"""Tests for FastAPI web application endpoints."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from argon2 import PasswordHasher
from fastapi.testclient import TestClient

from src.backend.web.app import create_app
from src.config import Settings

_ph = PasswordHasher()
TEST_HASH = _ph.hash("testpass")


@pytest.fixture()
def episodes_dir(tmp_path: Path) -> Path:
    """Create a temporary episodes directory with a dummy MP3."""
    ep_dir = tmp_path / "episodes"
    ep_dir.mkdir()
    dummy_mp3 = ep_dir / "test-episode.mp3"
    dummy_mp3.write_bytes(b"\xff\xfb\x90\x00" * 100)  # fake MP3 header bytes
    return ep_dir


@pytest.fixture()
def settings(episodes_dir: Path) -> Settings:
    """Create test Settings pointing to temporary episodes directory."""
    return Settings(
        google_api_key="test-key",
        base_url="https://podcast.example.com",
        vault_output_dir=str(episodes_dir.parent / "vault"),
        episodes_dir=str(episodes_dir),
        podcast_name="Test Podcast",
        REDACTED_FIELD_hash=TEST_HASH,
        session_secret_key="test-secret-key-for-testing",
    )


@pytest.fixture()
def client(settings: Settings) -> TestClient:
    """Create a FastAPI TestClient."""
    app = create_app(settings)
    return TestClient(app)


def test_static_mp3_serving(client: TestClient) -> None:
    """GET /episodes/{filename} returns 200 for existing MP3 file."""
    response = client.get("/episodes/test-episode.mp3")
    assert response.status_code == 200


def test_feed_endpoint(client: TestClient) -> None:
    """GET /feed.xml returns 200 with content-type application/rss+xml."""
    response = client.get("/feed.xml")
    assert response.status_code == 200
    assert "application/rss+xml" in response.headers["content-type"]


def test_feed_endpoint_content(client: TestClient) -> None:
    """GET /feed.xml returns valid RSS XML with correct podcast title."""
    response = client.get("/feed.xml")
    assert response.status_code == 200
    assert "Test Podcast" in response.text
    assert "<rss" in response.text
