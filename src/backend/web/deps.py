"""FastAPI dependencies for dashboard routes: DB session and HTTP Basic Auth."""

import secrets
from typing import Annotated, Generator

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from sqlalchemy.orm import Session

security = HTTPBasic()


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


def require_auth(
    credentials: Annotated[HTTPBasicCredentials, Depends(security)],
    request: Request,
) -> str:
    """Verify HTTP Basic credentials against dashboard settings.

    Returns the username on success; raises 401 on failure.
    """
    settings = request.app.state.settings
    username_ok = secrets.compare_digest(
        credentials.username.encode("utf-8"),
        settings.dashboard_username.encode("utf-8"),
    )
    password_ok = secrets.compare_digest(
        credentials.password.encode("utf-8"),
        settings.REDACTED_FIELD.encode("utf-8"),
    )
    if not (username_ok and password_ok):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username
