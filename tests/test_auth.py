"""Tests for HTTP Basic Auth password verification using Argon2id hashes.

Covers: valid credentials, wrong password, wrong username, no credentials,
        both wrong, and malformed hash resilience.
"""

import base64

import pytest
from argon2 import PasswordHasher
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.backend.web.app import create_app
from src.config import Settings
from src.infrastructure.database.models import Base

_ph = PasswordHasher()
VALID_HASH = _ph.hash("testpass")


def _basic_auth_header(username: str, password: str) -> dict:
    """Return an Authorization header dict for HTTP Basic Auth."""
    token = base64.b64encode(f"{username}:{password}".encode()).decode()
    return {"Authorization": f"Basic {token}"}


@pytest.fixture()
def settings(tmp_path):
    ep_dir = tmp_path / "episodes"
    ep_dir.mkdir()
    return Settings(
        google_api_key="k",
        base_url="https://x.com",
        vault_output_dir="/tmp",
        episodes_dir=str(ep_dir),
        REDACTED_FIELD_hash=VALID_HASH,
    )


@pytest.fixture()
def auth_client(settings):
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine)
    app = create_app(settings=settings, session_factory=factory)
    client = TestClient(app)
    yield client
    engine.dispose()


class TestPasswordVerification:
    """Verify require_auth uses Argon2id hash verification correctly."""

    def test_valid_credentials_return_200(self, auth_client):
        resp = auth_client.get(
            "/dashboard/hosts", headers=_basic_auth_header("admin", "testpass")
        )
        assert resp.status_code == 200

    def test_wrong_password_returns_401(self, auth_client):
        resp = auth_client.get(
            "/dashboard/hosts",
            headers=_basic_auth_header("admin", "wrongpassword"),
        )
        assert resp.status_code == 401

    def test_wrong_username_returns_401(self, auth_client):
        resp = auth_client.get(
            "/dashboard/hosts",
            headers=_basic_auth_header("baduser", "testpass"),
        )
        assert resp.status_code == 401

    def test_no_credentials_returns_401(self, auth_client):
        resp = auth_client.get("/dashboard/hosts")
        assert resp.status_code == 401

    def test_both_wrong_returns_401(self, auth_client):
        resp = auth_client.get(
            "/dashboard/hosts",
            headers=_basic_auth_header("baduser", "wrongpass"),
        )
        assert resp.status_code == 401

    def test_malformed_hash_returns_401_not_crash(self, auth_client):
        """A corrupted/invalid hash in config must return 401, not crash."""
        # Patch the settings object on the app to have a malformed hash
        auth_client.app.state.settings.REDACTED_FIELD_hash = (
            "$argon2id$v=19$CORRUPTED_HASH_DATA"
        )
        resp = auth_client.get(
            "/dashboard/hosts",
            headers=_basic_auth_header("admin", "testpass"),
        )
        assert resp.status_code == 401
