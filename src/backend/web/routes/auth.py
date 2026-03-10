"""Login, logout, and root redirect routes for session-based authentication."""

import secrets

from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError
from fastapi import APIRouter, Form, Request
from fastapi.responses import RedirectResponse
from starlette.responses import HTMLResponse, Response

from src.backend.web.deps import CSRFError, _ph, ensure_csrf_token

auth_router = APIRouter()


def _validate_next_url(next_url: str) -> str:
    """Validate next URL to prevent open redirect attacks.

    Only /dashboard/* paths are allowed; everything else falls back
    to /dashboard/episodes.
    """
    if next_url and next_url.startswith("/dashboard"):
        return next_url
    return "/dashboard/episodes"


@auth_router.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    """Render the branded login page, or redirect if already authenticated."""
    if request.session.get("user"):
        return RedirectResponse("/dashboard/episodes", status_code=303)

    # Generate CSRF token for the login form
    csrf_token = ensure_csrf_token(request)

    settings = request.app.state.settings
    templates = request.app.state.templates

    next_url = request.query_params.get("next", "")
    logged_out = request.query_params.get("logged_out", "")

    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context={
            "request": request,
            "next_url": next_url,
            "logged_out": logged_out,
            "podcast_name": settings.podcast_name,
            "podcast_cover_url": settings.podcast_cover_url,
            "csrf_token": csrf_token,
            "error": None,
        },
    )


@auth_router.post("/login")
def login_submit(
    request: Request,
    username: str = Form(""),
    password: str = Form(""),
):
    """Authenticate user credentials, set session, and redirect via HX-Redirect."""
    # Rate limit check -- before any credential processing
    limiter = request.app.state.rate_limiter
    client_ip = request.client.host if request.client else "unknown"
    allowed, retry_minutes = limiter.check(client_ip)
    if not allowed:
        return HTMLResponse(
            '<div class="login-alert login-alert--error">'
            f"Too many login attempts. Try again in {retry_minutes} minute(s)."
            "</div>",
            status_code=429,
        )

    # CSRF validation -- login uses custom error handling, not Depends(require_csrf)
    session_token = request.session.get("csrf_token", "")
    header_token = request.headers.get("X-CSRF-Token", "")
    if not session_token or not header_token or not secrets.compare_digest(session_token, header_token):
        raise CSRFError()

    settings = request.app.state.settings

    # Constant-time username comparison
    username_ok = secrets.compare_digest(
        username.encode(), settings.dashboard_username.encode()
    )

    password_ok = False
    if username_ok:
        try:
            password_ok = _ph.verify(settings.REDACTED_FIELD_hash, password)
        except (VerifyMismatchError, VerificationError, InvalidHashError):
            password_ok = False

    if not (username_ok and password_ok):
        # Record failed attempt for rate limiting
        limiter.record(client_ip)
        # Return error HTML fragment for HTMX swap into #login-error
        return HTMLResponse(
            '<div class="login-alert login-alert--error">'
            "Invalid username or password."
            "</div>",
            status_code=200,
        )

    # Set session and redirect -- regenerate CSRF token (session fixation prevention)
    request.session["user"] = username
    request.session["csrf_token"] = secrets.token_hex(32)
    next_url = _validate_next_url(request.query_params.get("next", ""))

    # HTMX POST needs 204 + HX-Redirect (not 3xx -- HTMX ignores headers on 3xx)
    response = Response(status_code=204)
    response.headers["HX-Redirect"] = next_url
    return response


@auth_router.post("/logout")
def logout(request: Request):
    """Clear the session and redirect to login with logged-out message.

    Requires valid CSRF token (sent via hx-headers on the HTMX button).
    """
    # CSRF validation for logout
    session_token = request.session.get("csrf_token", "")
    header_token = request.headers.get("X-CSRF-Token", "")
    if not session_token or not header_token or not secrets.compare_digest(session_token, header_token):
        raise CSRFError()

    request.session.clear()
    return RedirectResponse("/login?logged_out=1", status_code=303)


@auth_router.get("/")
def root_redirect(request: Request):
    """Redirect root URL based on authentication state."""
    if request.session.get("user"):
        return RedirectResponse("/dashboard/episodes", status_code=303)
    return RedirectResponse("/login", status_code=303)
