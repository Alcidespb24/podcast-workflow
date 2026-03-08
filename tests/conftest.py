from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from src.domain.models import Host, Style


@pytest.fixture()
def db_engine():
    """Create an in-memory SQLite engine for testing."""
    engine = create_engine("sqlite:///:memory:")
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
def tmp_env_file(tmp_path: Path) -> Path:
    """Write a temporary .env file with test configuration."""
    env_file = tmp_path / ".env"
    env_file.write_text(
        "GOOGLE_API_KEY=test-key-123\n"
        "DATABASE_URL=sqlite:///test.db\n"
    )
    return env_file
