---
phase: 07-http-hardening
plan: 01
subsystem: security
tags: [rate-limiting, security-headers, cors, csp, hsts, middleware]

requires:
  - phase: 06-auth-ui
    provides: Session-based login form with HTMX POST and CSRF protection
provides:
  - LoginRateLimiter class with per-IP tracking (5 attempts / 15 min window)
  - SecurityHeadersMiddleware adding 5 security headers to all responses
  - CORS configuration via CORS_ALLOWED_ORIGINS env var
  - RSS feed wildcard CORS (Access-Control-Allow-Origin: *)
affects: [08-csrf-hardening, deployment, production-config]

tech-stack:
  added: [starlette.middleware.cors.CORSMiddleware]
  patterns: [BaseHTTPMiddleware for response header injection, in-memory rate limiting with threading.Lock]

key-files:
  created:
    - src/backend/web/middleware/__init__.py
    - src/backend/web/middleware/rate_limit.py
    - src/backend/web/middleware/security_headers.py
    - tests/test_http_hardening.py
  modified:
    - src/backend/web/app.py
    - src/backend/web/routes/auth.py
    - src/config.py

key-decisions:
  - "Rate limit check runs before CSRF validation so blocked IPs get 429 immediately without needing valid token"
  - "RSS wildcard CORS handled in SecurityHeadersMiddleware (path check for /feed.xml) rather than separate middleware"

patterns-established:
  - "Middleware ordering: SessionMiddleware (inner) -> CORSMiddleware (conditional) -> SecurityHeadersMiddleware (outer, added last for LIFO)"
  - "Rate limiter stored on app.state for access from route handlers"

requirements-completed: [HTTP-01, HTTP-02, HTTP-03]

duration: 4min
completed: 2026-03-10
---

# Phase 7 Plan 01: HTTP Hardening Summary

**Login rate limiting (5 attempts/15min per IP), security headers (CSP, HSTS, X-Frame-Options, nosniff, Referrer-Policy), and configurable CORS with RSS wildcard**

## Performance

- **Duration:** 4 min
- **Started:** 2026-03-10T03:42:50Z
- **Completed:** 2026-03-10T03:47:09Z
- **Tasks:** 2
- **Files modified:** 7

## Accomplishments
- LoginRateLimiter blocks brute-force login after 5 failed attempts per IP within 15-minute window
- SecurityHeadersMiddleware adds X-Content-Type-Options, X-Frame-Options, Referrer-Policy, HSTS, and CSP to all responses
- CORS conditionally enabled via CORS_ALLOWED_ORIGINS env var; /feed.xml always gets wildcard CORS
- 12 tests: 4 unit (rate limiter logic) + 8 integration (headers, CORS, rate limit wiring)

## Task Commits

Each task was committed atomically:

1. **Task 1: Rate limiter, security headers, CORS config, and tests (TDD RED)** - `05dccb7` (test)
2. **Task 1+2: Wire middleware and rate limiter into app (TDD GREEN)** - `975bc6f` (feat)

## Files Created/Modified
- `src/backend/web/middleware/__init__.py` - Package init exporting LoginRateLimiter and SecurityHeadersMiddleware
- `src/backend/web/middleware/rate_limit.py` - In-memory rate limiter with per-IP tracking, thread-safe
- `src/backend/web/middleware/security_headers.py` - Adds 5 security headers + RSS wildcard CORS
- `src/config.py` - Added cors_allowed_origins field (maps to CORS_ALLOWED_ORIGINS env var)
- `src/backend/web/app.py` - Middleware stack wiring (SecurityHeaders, CORS, rate limiter on app.state)
- `src/backend/web/routes/auth.py` - Rate limit check before CSRF in login_submit, record on failure only
- `tests/test_http_hardening.py` - 12 tests covering all HTTP hardening requirements

## Decisions Made
- Rate limit check placed before CSRF validation so rate-limited IPs get 429 without needing a valid CSRF token
- RSS wildcard CORS handled in SecurityHeadersMiddleware via path check for /feed.xml rather than separate middleware
- SecurityHeadersMiddleware added last in add_middleware calls (LIFO) so it runs outermost

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] CSRF token handling in integration tests**
- **Found during:** Task 1 (GREEN phase)
- **Issue:** Integration tests POSTing to /login needed CSRF tokens since CSRF protection was added in a concurrent phase
- **Fix:** Added _get_csrf_token() and _post_login() helpers that GET /login first, extract CSRF token from meta tag, and include X-CSRF-Token header in POST requests
- **Files modified:** tests/test_http_hardening.py
- **Verification:** All 12 tests pass
- **Committed in:** 975bc6f

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** CSRF token handling required for tests due to concurrent phase work. No scope creep.

## Issues Encountered
- 3 pre-existing test_auth.py failures (logout CSRF, sidebar template change) from CSRF phase -- out of scope for this plan, not caused by HTTP hardening changes

## User Setup Required

Optional: Set `CORS_ALLOWED_ORIGINS` in .env if cross-origin access needed (comma-separated origins). Defaults to empty (same-origin only).

## Next Phase Readiness
- All HTTP hardening protections active
- Security headers on every response
- Rate limiting protects login endpoint
- CORS ready for cross-origin scenarios when configured

---
*Phase: 07-http-hardening*
*Completed: 2026-03-10*
