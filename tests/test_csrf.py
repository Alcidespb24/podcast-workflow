"""Tests for CSRF protection on state-changing endpoints.

Covers: token generation, validation, rejection of missing/invalid tokens,
        GET exemption, login/logout CSRF handling, token regeneration on login.
"""

import pytest
from argon2 import PasswordHasher
from fastapi import Request
from fastapi.testclient import TestClient
from starlette.responses import Response
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.backend.web.app import create_app
from src.config import Settings
from src.infrastructure.database.models import Base

_ph = PasswordHasher()
VALID_HASH = _ph.hash("testpass")


@pytest.fixture()
def settings(tmp_path):
    ep_dir = tmp_path / "episodes"
    ep_dir.mkdir()
    vault_dir = tmp_path / "vault"
    vault_dir.mkdir()
    return Settings(
        google_api_key="k",
        base_url="https://x.com",
        vault_base_dir=str(tmp_path),
        vault_output_dir=str(vault_dir),
        episodes_dir=str(ep_dir),
        dashboard_password_hash=VALID_HASH,
        session_secret_key="test-secret-key-for-csrf-testing",
    )


@pytest.fixture()
def app(settings):
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine)
    application = create_app(settings=settings, session_factory=factory)

    # Test-only route to establish authenticated session with CSRF token
    @application.get("/_test/login")
    def test_login(request: Request):
        import secrets as _s
        request.session["user"] = "admin"
        request.session["csrf_token"] = _s.token_hex(32)
        return Response("ok")

    # Test-only route to read CSRF token from session
    @application.get("/_test/csrf-token")
    def get_csrf_token(request: Request):
        return Response(request.session.get("csrf_token", ""))

    yield application
    engine.dispose()


@pytest.fixture()
def client(app):
    """Unauthenticated client."""
    return TestClient(app, base_url="https://testserver", follow_redirects=False)


@pytest.fixture()
def authed_client(app):
    """Client with authenticated session and CSRF token."""
    c = TestClient(app, base_url="https://testserver", follow_redirects=False)
    c.get("/_test/login")
    return c


def _get_csrf_token(client: TestClient) -> str:
    """Helper: read the CSRF token from session via test endpoint."""
    resp = client.get("/_test/csrf-token")
    return resp.text


class TestCSRFRejection:
    """CSRF protection rejects requests without valid tokens."""

    def test_csrf_rejects_missing_token(self, authed_client):
        """POST to CSRF-protected endpoint without X-CSRF-Token returns 403."""
        resp = authed_client.post(
            "/dashboard/hosts",
            data={"name": "TestHost", "voice": "Kore", "role": "host"},
        )
        assert resp.status_code == 403

    def test_csrf_rejects_invalid_token(self, authed_client):
        """POST with wrong X-CSRF-Token returns 403."""
        resp = authed_client.post(
            "/dashboard/hosts",
            data={"name": "TestHost", "voice": "Kore", "role": "host"},
            headers={"X-CSRF-Token": "invalid-token-value"},
        )
        assert resp.status_code == 403

    def test_csrf_accepts_valid_token(self, authed_client):
        """POST with valid X-CSRF-Token matching session token succeeds."""
        token = _get_csrf_token(authed_client)
        resp = authed_client.post(
            "/dashboard/hosts",
            data={"name": "TestHost", "voice": "Kore", "role": "host"},
            headers={"X-CSRF-Token": token},
        )
        assert resp.status_code == 200


class TestCSRFGetExemption:
    """GET requests are not subject to CSRF validation."""

    def test_get_requests_not_csrf_protected(self, authed_client):
        """GET to protected router succeeds without CSRF token."""
        resp = authed_client.get("/dashboard/hosts")
        assert resp.status_code == 200


class TestCSRFTokenGeneration:
    """CSRF token lifecycle in login flow."""

    def test_csrf_token_generated_on_login_page(self, client):
        """GET /login creates csrf_token in session."""
        client.get("/login")
        token = _get_csrf_token(client)
        assert token != ""
        assert len(token) == 64  # token_hex(32) produces 64 hex chars

    def test_csrf_token_regenerated_on_login_success(self, client):
        """After successful login, csrf_token changes (session fixation prevention)."""
        # Get initial token from login page
        client.get("/login")
        initial_token = _get_csrf_token(client)
        assert initial_token != ""

        # Login successfully -- must include CSRF token
        resp = client.post(
            "/login",
            data={"username": "admin", "password": "testpass"},
            headers={"X-CSRF-Token": initial_token},
        )
        assert resp.status_code == 204

        # Token should have changed
        new_token = _get_csrf_token(client)
        assert new_token != ""
        assert new_token != initial_token


class TestLoginCSRF:
    """CSRF protection on the login POST endpoint."""

    def test_login_post_with_csrf_succeeds(self, client):
        """POST /login with valid CSRF token and valid credentials succeeds."""
        client.get("/login")  # generates token
        token = _get_csrf_token(client)
        resp = client.post(
            "/login",
            data={"username": "admin", "password": "testpass"},
            headers={"X-CSRF-Token": token},
        )
        assert resp.status_code == 204
        assert "HX-Redirect" in resp.headers

    def test_login_post_without_csrf_rejected(self, client):
        """POST /login without CSRF token returns 403."""
        client.get("/login")  # generates token
        resp = client.post(
            "/login",
            data={"username": "admin", "password": "testpass"},
        )
        assert resp.status_code == 403


class TestLogoutCSRF:
    """CSRF handling on logout endpoint."""

    def test_logout_with_csrf_succeeds(self, authed_client):
        """POST /logout with valid CSRF token succeeds (303 redirect)."""
        token = _get_csrf_token(authed_client)
        resp = authed_client.post(
            "/logout",
            headers={"X-CSRF-Token": token},
        )
        assert resp.status_code == 303
        assert "/login" in resp.headers["location"]
