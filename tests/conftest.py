from datetime import datetime, timezone
from pathlib import Path

import pytest
from argon2 import PasswordHasher
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from src.backend.web.app import create_app
from src.config import Settings
from src.domain.models import Episode, Host, Style
from src.infrastructure.database.models import Base

_ph = PasswordHasher()
TEST_HASH = _ph.hash("testpass")


@pytest.fixture()
def db_engine():
    """Create an in-memory SQLite engine for testing.

    Uses StaticPool and check_same_thread=False so all threads
    (including FastAPI TestClient background threads) share the
    same in-memory database connection.
    """
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
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
    vault_output = tmp_path / "vault"
    vault_output.mkdir(exist_ok=True)
    env_file = tmp_path / ".env"
    env_file.write_text(
        "GOOGLE_API_KEY=test-key-123\n"
        "DATABASE_URL=sqlite:///test.db\n"
        "BASE_URL=https://example.com\n"
        f"VAULT_BASE_DIR={tmp_path}\n"
        f"VAULT_OUTPUT_DIR={vault_output}\n"
        f"DASHBOARD_PASSWORD_HASH={TEST_HASH}\n"
        "SESSION_SECRET_KEY=test-secret-key-for-testing\n"
    )
    return env_file


@pytest.fixture()
def dashboard_settings(tmp_path: Path) -> Settings:
    """Settings configured for dashboard testing."""
    ep_dir = tmp_path / "episodes"
    ep_dir.mkdir()
    vault_dir = tmp_path / "vault"
    vault_dir.mkdir(exist_ok=True)
    return Settings(
        google_api_key="test-key",
        base_url="https://podcast.example.com",
        vault_base_dir=str(tmp_path),
        vault_output_dir=str(vault_dir),
        episodes_dir=str(ep_dir),
        podcast_name="Test Podcast",
        dashboard_username="admin",
        dashboard_password_hash=TEST_HASH,
        session_secret_key="test-secret-key-for-testing",
    )


@pytest.fixture()
def session_factory(db_engine):
    """Create a sessionmaker bound to the test database engine."""
    return sessionmaker(bind=db_engine)


@pytest.fixture()
def dashboard_client(dashboard_settings: Settings, session_factory) -> TestClient:
    """Create a TestClient with an authenticated session for dashboard testing."""
    from fastapi import Request
    from starlette.responses import Response

    app = create_app(
        settings=dashboard_settings,
        session_factory=session_factory,
    )

    import secrets as _s

    _TEST_CSRF_TOKEN = _s.token_hex(32)

    # Add a test-only route to establish authenticated session with CSRF token
    @app.get("/_test/login")
    def test_login(request: Request):
        request.session["user"] = "admin"
        request.session["csrf_token"] = _TEST_CSRF_TOKEN
        return Response("ok")

    @app.get("/_test/csrf-token")
    def get_csrf_token(request: Request):
        return Response(request.session.get("csrf_token", ""))

    client = TestClient(app, base_url="https://testserver", follow_redirects=False)
    client.get("/_test/login")  # Sets session cookie on the client
    # Inject default CSRF header so all POST/PUT/DELETE requests pass CSRF check
    client.headers["X-CSRF-Token"] = _TEST_CSRF_TOKEN
    return client
