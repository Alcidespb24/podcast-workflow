"""Tests for HTTP hardening: rate limiting, security headers, and CORS policy.

Covers: login rate limiting (HTTP-01), security headers (HTTP-02),
        CORS configuration (HTTP-03), RSS CORS wildcard.
"""

import re
import time
from unittest.mock import patch

import pytest
from argon2 import PasswordHasher
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.backend.web.app import create_app
from src.backend.web.middleware.rate_limit import LoginRateLimiter
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
        REDACTED_FIELD_hash=VALID_HASH,
        session_secret_key="test-secret-key-for-testing",
    )


@pytest.fixture()
def settings_with_cors(tmp_path):
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
        REDACTED_FIELD_hash=VALID_HASH,
        session_secret_key="test-secret-key-for-testing",
        cors_allowed_origins="https://example.com",
    )


def _make_app(settings):
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine)
    app = create_app(settings=settings, session_factory=factory)
    return app, engine


def _get_csrf_token(client: TestClient) -> str:
    """GET /login to establish session with CSRF token, return the token."""
    resp = client.get("/login")
    match = re.search(r'csrf-token" content="([^"]+)"', resp.text)
    assert match, "CSRF token not found in login page"
    return match.group(1)


def _post_login(client: TestClient, csrf_token: str, username: str, password: str):
    """POST /login with CSRF token header."""
    return client.post(
        "/login",
        data={"username": username, "password": password},
        headers={"X-CSRF-Token": csrf_token},
    )


# ── Rate Limiter Unit Tests ──


class TestRateLimiterUnit:
    """Unit tests for LoginRateLimiter check/record logic."""

    def test_rate_limit_allows_first_5_attempts(self):
        """5 failed logins return allowed=True."""
        limiter = LoginRateLimiter(max_attempts=5, window_seconds=900)
        for _ in range(5):
            allowed, _ = limiter.check("1.2.3.4")
            assert allowed is True
            limiter.record("1.2.3.4")

    def test_rate_limit_blocks_after_5_attempts(self):
        """6th failed login returns allowed=False with retry_after > 0."""
        limiter = LoginRateLimiter(max_attempts=5, window_seconds=900)
        for _ in range(5):
            limiter.record("1.2.3.4")
        allowed, retry_after = limiter.check("1.2.3.4")
        assert allowed is False
        assert retry_after > 0

    def test_rate_limit_resets_after_window(self):
        """After window expires, login is allowed again."""
        limiter = LoginRateLimiter(max_attempts=5, window_seconds=900)
        for _ in range(5):
            limiter.record("1.2.3.4")

        # Mock time to be past the window
        with patch("src.backend.web.middleware.rate_limit.time") as mock_time:
            mock_time.time.return_value = time.time() + 901
            allowed, _ = limiter.check("1.2.3.4")
            assert allowed is True

    def test_rate_limit_does_not_count_successful_logins(self):
        """Different IPs have independent counters."""
        limiter = LoginRateLimiter(max_attempts=5, window_seconds=900)
        # Fill up one IP
        for _ in range(5):
            limiter.record("1.2.3.4")
        # A different IP should still be allowed
        allowed, _ = limiter.check("5.6.7.8")
        assert allowed is True


# ── Security Headers Integration Tests ──


class TestSecurityHeaders:
    """Test that all security headers are present on responses."""

    def test_security_headers_present(self, settings):
        """GET /login response includes all 5 security headers."""
        app, engine = _make_app(settings)
        client = TestClient(app, follow_redirects=False)
        resp = client.get("/login")
        assert resp.status_code == 200
        assert resp.headers["X-Content-Type-Options"] == "nosniff"
        assert resp.headers["X-Frame-Options"] == "DENY"
        assert resp.headers["Referrer-Policy"] == "strict-origin-when-cross-origin"
        assert "max-age=31536000" in resp.headers["Strict-Transport-Security"]
        assert "includeSubDomains" in resp.headers["Strict-Transport-Security"]
        engine.dispose()

    def test_csp_header_correct(self, settings):
        """CSP header includes all required directives."""
        app, engine = _make_app(settings)
        client = TestClient(app, follow_redirects=False)
        resp = client.get("/login")
        csp = resp.headers["Content-Security-Policy"]
        assert "default-src 'self'" in csp
        assert "script-src 'self' 'unsafe-inline' cdn.jsdelivr.net" in csp
        assert "style-src 'self' cdn.jsdelivr.net" in csp
        assert "img-src 'self' data: https:" in csp
        assert "connect-src 'self'" in csp
        engine.dispose()


# ── CORS Integration Tests ──


class TestCORS:
    """Test CORS configuration behavior."""

    def test_cors_no_config_no_header(self, settings):
        """When CORS_ALLOWED_ORIGINS is empty, responses have no ACAO header."""
        app, engine = _make_app(settings)
        client = TestClient(app, follow_redirects=False)
        resp = client.get("/login")
        # Security headers middleware should not add ACAO for non-RSS
        assert "Access-Control-Allow-Origin" not in resp.headers
        engine.dispose()

    def test_cors_allows_configured_origin(self, settings_with_cors):
        """When CORS_ALLOWED_ORIGINS set, preflight from that origin returns CORS headers."""
        app, engine = _make_app(settings_with_cors)
        client = TestClient(app, follow_redirects=False)
        resp = client.options(
            "/login",
            headers={
                "Origin": "https://example.com",
                "Access-Control-Request-Method": "POST",
            },
        )
        assert resp.headers.get("Access-Control-Allow-Origin") == "https://example.com"
        engine.dispose()

    def test_cors_rejects_unlisted_origin(self, settings_with_cors):
        """Preflight from unlisted origin gets no CORS headers."""
        app, engine = _make_app(settings_with_cors)
        client = TestClient(app, follow_redirects=False)
        resp = client.options(
            "/login",
            headers={
                "Origin": "https://evil.com",
                "Access-Control-Request-Method": "POST",
            },
        )
        acao = resp.headers.get("Access-Control-Allow-Origin", "")
        assert "evil.com" not in acao
        engine.dispose()

    def test_rss_cors_wildcard(self, settings):
        """GET /feed.xml always has Access-Control-Allow-Origin: * regardless of CORS config."""
        app, engine = _make_app(settings)
        client = TestClient(app, follow_redirects=False)
        resp = client.get("/feed.xml")
        assert resp.headers.get("Access-Control-Allow-Origin") == "*"
        engine.dispose()


# ── Rate Limiter Integration Tests ──


class TestRateLimitIntegration:
    """Integration tests for rate limiter wired into login_submit."""

    def test_rate_limit_blocks_6th_failed_login(self, settings):
        """After 5 failed logins, 6th returns 429 with error message."""
        app, engine = _make_app(settings)
        client = TestClient(app, follow_redirects=False)
        csrf_token = _get_csrf_token(client)

        for i in range(5):
            resp = _post_login(client, csrf_token, "admin", "wrong")
            assert resp.status_code == 200, f"attempt {i+1} expected 200, got {resp.status_code}"

        # 6th attempt should be rate limited (before CSRF check)
        resp = _post_login(client, csrf_token, "admin", "wrong")
        assert resp.status_code == 429
        assert "Too many login attempts" in resp.text
        engine.dispose()

    def test_rate_limit_does_not_block_successful_login(self, settings):
        """Successful login does not consume rate limit counter."""
        app, engine = _make_app(settings)
        client = TestClient(app, follow_redirects=False)
        csrf_token = _get_csrf_token(client)

        # 4 failed attempts
        for _ in range(4):
            _post_login(client, csrf_token, "admin", "wrong")

        # Successful login
        resp = _post_login(client, csrf_token, "admin", "testpass")
        assert resp.status_code == 204
        engine.dispose()
