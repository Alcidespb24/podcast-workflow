"""Tests for session-based authentication using Starlette SessionMiddleware.

Covers: session config fields, unauthenticated redirects, HTMX auth handling,
        authenticated access, status endpoint auth (AUTH-08), session expiry (AUTH-07),
        and next URL validation.
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
    return Settings(
        google_api_key="k",
        base_url="https://x.com",
        vault_output_dir="/tmp",
        episodes_dir=str(ep_dir),
        REDACTED_FIELD_hash=VALID_HASH,
        session_secret_key="test-secret-key-for-testing",
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

    # Add a test-only route to establish authenticated session
    @application.get("/_test/login")
    def test_login(request: Request):
        request.session["user"] = "admin"
        return Response("ok")

    yield application
    engine.dispose()


@pytest.fixture()
def auth_client(app):
    """Unauthenticated client (no session)."""
    return TestClient(app, follow_redirects=False)


@pytest.fixture()
def authed_client(app):
    """Client with an authenticated session cookie."""
    client = TestClient(app, follow_redirects=False)
    client.get("/_test/login")  # Sets session cookie on the client
    return client


class TestSessionConfig:
    """Test that Settings accepts session configuration fields."""

    def test_session_secret_key_required(self, tmp_path):
        """Settings without SESSION_SECRET_KEY raises ValidationError."""
        ep_dir = tmp_path / "episodes"
        ep_dir.mkdir()
        with pytest.raises(Exception):
            Settings(
                _env_file="",
                google_api_key="k",
                base_url="https://x.com",
                vault_output_dir="/tmp",
                episodes_dir=str(ep_dir),
                REDACTED_FIELD_hash=VALID_HASH,
                # session_secret_key intentionally omitted
            )

    def test_session_timeout_hours_default(self, settings):
        """SESSION_TIMEOUT_HOURS defaults to 168 (7 days)."""
        assert settings.session_timeout_hours == 168


class TestSessionAuth:
    """Test session-based authentication replaces HTTP Basic Auth (AUTH-04)."""

    def test_unauthenticated_dashboard_redirects_to_login(self, auth_client):
        """Unauthenticated GET /dashboard/hosts returns redirect to /login (303)."""
        resp = auth_client.get("/dashboard/hosts")
        assert resp.status_code == 303
        assert "/login" in resp.headers["location"]

    def test_authenticated_session_allows_access(self, authed_client):
        """Authenticated session allows access to /dashboard/hosts (200)."""
        resp = authed_client.get("/dashboard/hosts")
        assert resp.status_code == 200


class TestHTMXAuthRedirect:
    """Test HTMX-specific auth redirect behavior."""

    def test_unauthenticated_htmx_returns_204_with_hx_redirect(self, auth_client):
        """Unauthenticated HTMX request returns 204 with HX-Redirect header."""
        resp = auth_client.get(
            "/dashboard/hosts",
            headers={"HX-Request": "true"},
        )
        assert resp.status_code == 204
        assert "HX-Redirect" in resp.headers
        assert "/login" in resp.headers["HX-Redirect"]

    def test_htmx_with_current_url_builds_next_param(self, auth_client):
        """HTMX request with HX-Current-URL builds ?next= from dashboard path."""
        resp = auth_client.get(
            "/dashboard/hosts",
            headers={
                "HX-Request": "true",
                "HX-Current-URL": "https://localhost/dashboard/styles",
            },
        )
        assert resp.status_code == 204
        redirect_url = resp.headers["HX-Redirect"]
        assert "/login" in redirect_url
        assert "next=/dashboard/styles" in redirect_url


class TestStatusEndpointAuth:
    """Test /dashboard/status requires authentication (AUTH-08)."""

    def test_unauthenticated_status_redirects_to_login(self, auth_client):
        """Unauthenticated GET /dashboard/status returns redirect to /login (303)."""
        resp = auth_client.get("/dashboard/status")
        assert resp.status_code == 303
        assert "/login" in resp.headers["location"]

    def test_authenticated_status_returns_200(self, authed_client):
        """Authenticated session allows access to /dashboard/status (200)."""
        resp = authed_client.get("/dashboard/status")
        assert resp.status_code == 200


class TestSessionExpiry:
    """Test session expiry behavior (AUTH-07)."""

    def test_session_timeout_is_configurable(self, tmp_path):
        """SESSION_TIMEOUT_HOURS can be set to a custom value."""
        ep_dir = tmp_path / "episodes"
        ep_dir.mkdir()
        settings = Settings(
            google_api_key="k",
            base_url="https://x.com",
            vault_output_dir="/tmp",
            episodes_dir=str(ep_dir),
            REDACTED_FIELD_hash=VALID_HASH,
            session_secret_key="test-secret",
            session_timeout_hours=24,
        )
        assert settings.session_timeout_hours == 24


class TestNextUrlValidation:
    """Test that ?next= URL in redirects is safe."""

    def test_dashboard_path_preserved_in_redirect(self, auth_client):
        """Redirect for /dashboard/hosts includes next=/dashboard/hosts."""
        resp = auth_client.get("/dashboard/hosts")
        assert resp.status_code == 303
        assert "next=/dashboard/hosts" in resp.headers["location"]

    def test_non_dashboard_path_not_included(self, auth_client):
        """HTMX request with non-dashboard HX-Current-URL does not include next param."""
        resp = auth_client.get(
            "/dashboard/hosts",
            headers={
                "HX-Request": "true",
                "HX-Current-URL": "https://evil.com/steal",
            },
        )
        assert resp.status_code == 204
        redirect_url = resp.headers["HX-Redirect"]
        assert "evil.com" not in redirect_url


# ── Plan 06-02: Login / Logout / Root Redirect ──


class TestLoginPage:
    """Test GET /login renders the login form."""

    def test_login_page_returns_200_with_form(self, auth_client):
        """GET /login returns 200 with HTML containing login form."""
        resp = auth_client.get("/login")
        assert resp.status_code == 200
        body = resp.text
        assert "username" in body
        assert "password" in body
        assert "Sign in" in body

    def test_login_page_redirects_authenticated_user(self, authed_client):
        """GET /login when already authenticated redirects to /dashboard/episodes (303)."""
        resp = authed_client.get("/login")
        assert resp.status_code == 303
        assert "/dashboard/episodes" in resp.headers["location"]

    def test_login_page_shows_logged_out_message(self, auth_client):
        """GET /login?logged_out=1 shows 'You've been logged out' message."""
        resp = auth_client.get("/login?logged_out=1")
        assert resp.status_code == 200
        assert "logged out" in resp.text.lower()


class TestLoginSubmission:
    """Test POST /login authentication flow."""

    def test_valid_credentials_sets_session_and_redirects(self, auth_client):
        """POST /login with valid credentials sets session and returns 204 with HX-Redirect."""
        resp = auth_client.post(
            "/login",
            data={"username": "admin", "password": "testpass"},
        )
        assert resp.status_code == 204
        assert "HX-Redirect" in resp.headers
        assert "/dashboard/episodes" in resp.headers["HX-Redirect"]

    def test_invalid_credentials_returns_error(self, auth_client):
        """POST /login with invalid credentials returns 200 with error message."""
        resp = auth_client.post(
            "/login",
            data={"username": "admin", "password": "wrongpass"},
        )
        assert resp.status_code == 200
        assert "Invalid username or password" in resp.text

    def test_next_param_preserved_on_login(self, auth_client):
        """POST /login with ?next=/dashboard/hosts returns HX-Redirect to /dashboard/hosts."""
        resp = auth_client.post(
            "/login?next=/dashboard/hosts",
            data={"username": "admin", "password": "testpass"},
        )
        assert resp.status_code == 204
        assert "/dashboard/hosts" in resp.headers["HX-Redirect"]

    def test_open_redirect_prevention(self, auth_client):
        """POST /login with ?next=https://evil.com redirects to /dashboard/episodes."""
        resp = auth_client.post(
            "/login?next=https://evil.com",
            data={"username": "admin", "password": "testpass"},
        )
        assert resp.status_code == 204
        assert "/dashboard/episodes" in resp.headers["HX-Redirect"]
        assert "evil.com" not in resp.headers["HX-Redirect"]


class TestLogout:
    """Test POST /logout session invalidation."""

    def test_logout_clears_session_and_redirects(self, authed_client):
        """POST /logout clears session and redirects to /login?logged_out=1 (303)."""
        resp = authed_client.post("/logout")
        assert resp.status_code == 303
        assert "/login" in resp.headers["location"]
        assert "logged_out=1" in resp.headers["location"]

    def test_logout_invalidates_session(self, authed_client):
        """POST /logout -- subsequent request to /dashboard/hosts is rejected."""
        authed_client.post("/logout")
        resp = authed_client.get("/dashboard/hosts")
        assert resp.status_code == 303
        assert "/login" in resp.headers["location"]


class TestRootRedirect:
    """Test GET / redirects based on auth state."""

    def test_root_unauthenticated_redirects_to_login(self, auth_client):
        """GET / redirects to /login (303) when unauthenticated."""
        resp = auth_client.get("/")
        assert resp.status_code == 303
        assert "/login" in resp.headers["location"]

    def test_root_authenticated_redirects_to_dashboard(self, authed_client):
        """GET / redirects to /dashboard/episodes (303) when authenticated."""
        resp = authed_client.get("/")
        assert resp.status_code == 303
        assert "/dashboard/episodes" in resp.headers["location"]


class TestSidebarLogout:
    """Test logout button is present in sidebar on dashboard pages."""

    def test_sidebar_contains_logout_form(self, authed_client):
        """GET /dashboard/hosts (authenticated) includes logout form in sidebar."""
        resp = authed_client.get("/dashboard/hosts")
        assert resp.status_code == 200
        body = resp.text
        assert 'action="/logout"' in body
        assert "Log out" in body
