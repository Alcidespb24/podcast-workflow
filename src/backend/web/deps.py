"""FastAPI dependencies for dashboard routes: DB session and session-based auth."""

import secrets
from typing import Generator
from urllib.parse import urlparse

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError
from fastapi import Request
from sqlalchemy.orm import Session

_ph = PasswordHasher()


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
