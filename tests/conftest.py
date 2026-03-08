import base64
from datetime import datetime, timezone
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from src.backend.web.app import create_app
from src.config import Settings
from src.domain.models import Episode, Host, Style
from src.infrastructure.database.models import Base


@pytest.fixture()
def db_engine():
    """Create an in-memory SQLite engine for testing."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    yield engine
    engine.dispose()


@pytest.fixture()
def db_session(db_engine):
    """Create a database session that rolls back after each test."""
    with Session(db_engine) as session:
        yield session
        session.rollback()


@pytest.fixture()
def sample_host_a() -> Host:
    """Return a sample primary host."""
    return Host(name="Joe", voice="Kore", role="host")


@pytest.fixture()
def sample_host_b() -> Host:
    """Return a sample co-host."""
    return Host(name="Jane", voice="Puck", role="co-host")


@pytest.fixture()
def sample_style() -> Style:
    """Return a sample default style."""
    return Style(name="Default", tone="Informative & engaging")


@pytest.fixture()
def sample_episode() -> Episode:
    """Return a sample episode for testing."""
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
def tmp_env_file(tmp_path: Path) -> Path:
    """Write a temporary .env file with test configuration."""
    env_file = tmp_path / ".env"
    env_file.write_text(
        "GOOGLE_API_KEY=test-key-123\n"
        "DATABASE_URL=sqlite:///test.db\n"
        "BASE_URL=https://example.com\n"
        "VAULT_OUTPUT_DIR=/tmp/vault\n"
    )
    return env_file


@pytest.fixture()
def dashboard_settings(tmp_path: Path) -> Settings:
    """Settings configured for dashboard testing."""
    ep_dir = tmp_path / "episodes"
    ep_dir.mkdir()
    return Settings(
        google_api_key="test-key",
        base_url="https://podcast.example.com",
        vault_output_dir=str(tmp_path / "vault"),
        episodes_dir=str(ep_dir),
        podcast_name="Test Podcast",
        dashboard_username="admin",
        REDACTED_FIELD="testpass",
    )


@pytest.fixture()
def session_factory(db_engine):
    """Create a sessionmaker bound to the test database engine."""
    return sessionmaker(bind=db_engine)


@pytest.fixture()
def dashboard_client(dashboard_settings: Settings, session_factory) -> TestClient:
    """Create a TestClient with Basic Auth for dashboard testing."""
    app = create_app(
        settings=dashboard_settings,
        session_factory=session_factory,
    )
    client = TestClient(app)
    credentials = base64.b64encode(b"admin:testpass").decode("ascii")
    client.headers["Authorization"] = f"Basic {credentials}"
    return client
