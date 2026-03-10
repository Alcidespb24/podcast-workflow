"""Security headers middleware for all HTTP responses."""

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to every HTTP response.

    Headers: X-Content-Type-Options, X-Frame-Options, Referrer-Policy,
    Strict-Transport-Security, Content-Security-Policy.
    Also adds Access-Control-Allow-Origin: * for the /feed.xml endpoint.
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)

        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Strict-Transport-Security"] = (
            "max-age=31536000; includeSubDomains"
        )
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' cdn.jsdelivr.net; "
            "style-src 'self' cdn.jsdelivr.net; "
            "img-src 'self' data: https:; "
            "connect-src 'self'"
        )

        # RSS feed gets wildcard CORS for podcast clients
        if request.url.path == "/feed.xml":
            response.headers["Access-Control-Allow-Origin"] = "*"

        return response
