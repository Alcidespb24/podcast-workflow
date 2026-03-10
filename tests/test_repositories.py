"""Tests for database repositories and seed_defaults."""

import pytest
from argon2 import PasswordHasher
from sqlalchemy.orm import Session

from src.config import Settings
from src.domain.models import Host, Style
from src.infrastructure.database.models import Base
from src.infrastructure.database.repositories import (
    HostRepository,
    StyleRepository,
    seed_defaults,
)

_ph = PasswordHasher()
TEST_HASH = _ph.hash("testpass")


@pytest.fixture(autouse=True)
def _create_tables(db_engine):
    """Create all tables before each test, drop after."""
    Base.metadata.create_all(db_engine)
    yield
    Base.metadata.drop_all(db_engine)


# ── Host CRUD ──────────────────────────────────────────────────────────


def test_host_create(db_session: Session) -> None:
    repo = HostRepository(db_session)
    host = repo.create(Host(name="Alice", voice="Aria", role="host"))
    assert host.id is not None
    assert host.name == "Alice"
    assert host.voice == "Aria"
    assert host.role == "host"


def test_host_get_by_id(db_session: Session) -> None:
    repo = HostRepository(db_session)
    created = repo.create(Host(name="Bob", voice="Kore", role="host"))
    fetched = repo.get_by_id(created.id)
    assert fetched is not None
    assert fetched.name == "Bob"


def test_host_get_by_id_not_found(db_session: Session) -> None:
    repo = HostRepository(db_session)
    assert repo.get_by_id(9999) is None


def test_host_get_defaults(db_session: Session) -> None:
    repo = HostRepository(db_session)
    repo.create(Host(name="A", voice="V1", role="host"))
    settings = Settings(
        google_api_key="k",
        database_url="sqlite:///:memory:",
        base_url="https://example.com",
        vault_output_dir="/tmp/vault",
        REDACTED_FIELD_hash=TEST_HASH,
        session_secret_key="test-secret",
    )
    seed_defaults(db_session, settings)
    defaults = repo.get_defaults()
    assert len(defaults) == 0  # table was non-empty so seed did nothing

    # Fresh session with empty table
    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session as SA_Session

    engine2 = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine2)
    with SA_Session(engine2) as s2:
        seed_defaults(s2, settings)
        s2.commit()
        repo2 = HostRepository(s2)
        defaults2 = repo2.get_defaults()
        assert len(defaults2) == 2
    engine2.dispose()


def test_host_get_all(db_session: Session) -> None:
    repo = HostRepository(db_session)
    repo.create(Host(name="H1", voice="V1", role="host"))
    repo.create(Host(name="H2", voice="V2", role="co-host"))
    all_hosts = repo.get_all()
    assert len(all_hosts) == 2


def test_host_update(db_session: Session) -> None:
    repo = HostRepository(db_session)
    created = repo.create(Host(name="Old", voice="V1", role="host"))
    updated = repo.update(created.id, name="New", voice="V2")
    assert updated is not None
    assert updated.name == "New"
    assert updated.voice == "V2"


def test_host_update_rejects_unknown_field(db_session: Session) -> None:
    repo = HostRepository(db_session)
    created = repo.create(Host(name="Safe", voice="V1", role="host"))
    with pytest.raises(ValueError, match="Unknown Host fields"):
        repo.update(created.id, nonexistent="bad")


def test_host_delete(db_session: Session) -> None:
    repo = HostRepository(db_session)
    created = repo.create(Host(name="Doomed", voice="V1", role="host"))
    assert repo.delete(created.id) is True
    assert repo.get_by_id(created.id) is None
    assert repo.delete(9999) is False


def test_host_returns_domain_model(db_session: Session) -> None:
    repo = HostRepository(db_session)
    host = repo.create(Host(name="DM", voice="V", role="host"))
    assert isinstance(host, Host)
    fetched = repo.get_by_id(host.id)
    assert isinstance(fetched, Host)


# ── Style CRUD ─────────────────────────────────────────────────────────


def test_style_create(db_session: Session) -> None:
    repo = StyleRepository(db_session)
    style = repo.create(Style(name="Casual", tone="Relaxed"))
    assert style.id is not None
    assert style.name == "Casual"
    assert style.tone == "Relaxed"
    assert style.personality_guidance is None


def test_style_create_with_personality_guidance(db_session: Session) -> None:
    repo = StyleRepository(db_session)
    style = repo.create(
        Style(name="Deep", tone="Serious", personality_guidance="Be thoughtful")
    )
    assert style.personality_guidance == "Be thoughtful"


def test_style_get_defaults(db_session: Session) -> None:
    repo = StyleRepository(db_session)
    settings = Settings(
        google_api_key="k",
        database_url="sqlite:///:memory:",
        base_url="https://example.com",
        vault_output_dir="/tmp/vault",
        REDACTED_FIELD_hash=TEST_HASH,
        session_secret_key="test-secret",
    )
    seed_defaults(db_session, settings)
    defaults = repo.get_defaults()
    assert len(defaults) == 1
    assert defaults[0].name == "Default"


def test_style_update(db_session: Session) -> None:
    repo = StyleRepository(db_session)
    created = repo.create(Style(name="OldStyle", tone="Boring"))
    updated = repo.update(created.id, tone="Exciting")
    assert updated is not None
    assert updated.tone == "Exciting"


def test_style_update_rejects_unknown_field(db_session: Session) -> None:
    repo = StyleRepository(db_session)
    created = repo.create(Style(name="Safe", tone="OK"))
    with pytest.raises(ValueError, match="Unknown Style fields"):
        repo.update(created.id, nonexistent="bad")


def test_style_delete(db_session: Session) -> None:
    repo = StyleRepository(db_session)
    created = repo.create(Style(name="Gone", tone="Meh"))
    assert repo.delete(created.id) is True
    assert repo.get_by_id(created.id) is None
    assert repo.delete(9999) is False


def test_style_returns_domain_model(db_session: Session) -> None:
    repo = StyleRepository(db_session)
    style = repo.create(Style(name="SM", tone="T"))
    assert isinstance(style, Style)
    fetched = repo.get_by_id(style.id)
    assert isinstance(fetched, Style)


# ── Seed defaults ──────────────────────────────────────────────────────


def test_seed_defaults_creates_hosts_and_style(db_session: Session) -> None:
    settings = Settings(
        google_api_key="k",
        database_url="sqlite:///:memory:",
        base_url="https://example.com",
        vault_output_dir="/tmp/vault",
        REDACTED_FIELD_hash=TEST_HASH,
        session_secret_key="test-secret",
    )
    seed_defaults(db_session, settings)
    host_repo = HostRepository(db_session)
    style_repo = StyleRepository(db_session)

    hosts = host_repo.get_all()
    assert len(hosts) == 2
    assert hosts[0].name == "Joe"
    assert hosts[0].voice == "Kore"
    assert hosts[1].name == "Jane"
    assert hosts[1].voice == "Puck"

    styles = style_repo.get_all()
    assert len(styles) == 1
    assert styles[0].tone == "Informative & engaging"


def test_seed_defaults_idempotent(db_session: Session) -> None:
    settings = Settings(
        google_api_key="k",
        database_url="sqlite:///:memory:",
        base_url="https://example.com",
        vault_output_dir="/tmp/vault",
        REDACTED_FIELD_hash=TEST_HASH,
        session_secret_key="test-secret",
    )
    seed_defaults(db_session, settings)
    seed_defaults(db_session, settings)

    host_repo = HostRepository(db_session)
    assert len(host_repo.get_all()) == 2

    style_repo = StyleRepository(db_session)
    assert len(style_repo.get_all()) == 1
