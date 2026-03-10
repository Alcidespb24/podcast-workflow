"""FastAPI dependencies for dashboard routes: DB session and session-based auth."""

import secrets
from typing import Generator
from urllib.parse import urlparse

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError
from fastapi import Request
from sqlalchemy.orm import Session

_ph = PasswordHasher()


class CSRFError(Exception):
    """Raised when CSRF token validation fails.

    The exception handler in app.py converts this into a 403 response
    (plain text for normal requests, HX-Reswap toast for HTMX requests).
    """


class AuthRequired(Exception):
    """Raised when a request lacks a valid session.

    The exception handler in app.py converts this into a redirect to /login
    (303 for normal requests, 204 + HX-Redirect for HTMX requests).
    """

    def __init__(self, next_url: str = ""):
        self.next_url = next_url


def get_db(request: Request) -> Generator[Session, None, None]:
    """Yield a SQLAlchemy session with commit-on-success and rollback-on-error."""
    session_factory = request.app.state.session_factory
    session = session_factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def require_auth(request: Request) -> str:
    """Check session for authenticated user. Raise AuthRequired if missing.

    For HTMX requests, extracts the current dashboard path from HX-Current-URL
    to build a ?next= parameter for the login redirect.

    Returns the username on success.
    """
    user = request.session.get("user")
    if user:
        return user

    # Determine next_url for redirect back after login
    next_url = ""

    if request.headers.get("HX-Request"):
        # HTMX request: extract path from HX-Current-URL header
        current_url = request.headers.get("HX-Current-URL", "")
        if current_url:
            parsed = urlparse(current_url)
            if parsed.path.startswith("/dashboard"):
                next_url = parsed.path
    else:
        # Normal request: use the request path directly
        if request.url.path.startswith("/dashboard"):
            next_url = request.url.path

    raise AuthRequired(next_url=next_url)


def require_csrf(request: Request) -> None:
    """Validate X-CSRF-Token header against session csrf_token.

    Applied as a router-level dependency. Automatically skips safe HTTP
    methods (GET, HEAD, OPTIONS) so only state-changing requests are checked.

    Raises CSRFError if token is missing, empty, or mismatched.
    """
    if request.method in ("GET", "HEAD", "OPTIONS"):
        return
    session_token = request.session.get("csrf_token", "")
    header_token = request.headers.get("X-CSRF-Token", "")
    if not session_token or not header_token:
        raise CSRFError()
    if not secrets.compare_digest(session_token, header_token):
        raise CSRFError()


def ensure_csrf_token(request: Request) -> str:
    """Ensure a CSRF token exists in the session, creating one if needed.

    Called by template-rendering routes so the meta tag always has a value.
    Returns the token string.
    """
    token = request.session.get("csrf_token")
    if not token:
        token = secrets.token_hex(32)
        request.session["csrf_token"] = token
    return token
