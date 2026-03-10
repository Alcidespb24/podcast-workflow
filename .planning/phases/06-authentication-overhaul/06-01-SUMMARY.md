---
phase: 06-authentication-overhaul
plan: 01
subsystem: auth
tags: [session-auth, starlette, session-middleware, signed-cookies, htmx-redirect]

# Dependency graph
requires:
  - phase: 05-secrets-and-configuration-foundation
    provides: Settings with REDACTED_FIELD_hash (Argon2id validated), PasswordHasher in deps.py
provides:
  - SessionMiddleware with signed cookie sessions on FastAPI app
  - AuthRequired exception with HTMX-aware redirect handler
  - Session-based require_auth dependency (replaces HTTP Basic Auth entirely)
  - status_router secured with session auth (AUTH-08)
  - session_secret_key (required) and session_timeout_hours (configurable) in Settings
  - Session-based test infrastructure (conftest.py dashboard_client, test_auth.py test suite)
affects: [06-02-login-logout-ui, 07-http-hardening]

# Tech tracking
tech-stack:
  added: []
  patterns: [session-middleware-signed-cookies, auth-required-exception-handler, htmx-204-hx-redirect, test-only-login-route-fixture]

key-files:
  created: []
  modified:
    - src/config.py
    - src/backend/web/deps.py
    - src/backend/web/app.py
    - src/backend/web/routes/dashboard.py
    - .env.example
    - tests/test_auth.py
    - tests/conftest.py
    - tests/test_config.py
    - tests/test_dashboard_episodes.py
    - tests/test_dashboard_hosts.py
    - tests/test_dashboard_presets.py
    - tests/test_dashboard_styles.py
    - tests/test_web_app.py
    - tests/test_podcast_service.py
    - tests/test_repositories.py

key-decisions:
  - "Used AuthRequired exception + exception handler pattern instead of returning Response from dependency (avoids Pitfall 5 from RESEARCH.md)"
  - "Test-only /_test/login route pattern for setting session in test fixtures (cleanest approach, no itsdangerous manipulation needed)"

patterns-established:
  - "AuthRequired exception handler: normal requests get 303 redirect to /login, HTMX requests get 204 + HX-Redirect header"
  - "Test session fixture: add /_test/login route to app, call it from TestClient to establish session cookie"
  - "require_auth extracts next_url from request path (normal) or HX-Current-URL header (HTMX), only for /dashboard paths"

requirements-completed: [AUTH-04, AUTH-07, AUTH-08]

# Metrics
duration: 7min
completed: 2026-03-10
---

# Phase 6 Plan 01: Session Infrastructure Summary

**Session-based auth via Starlette SessionMiddleware replacing HTTP Basic Auth, with AuthRequired exception handler providing HTMX-aware redirects and configurable 7-day timeout**

## Performance

- **Duration:** 7 min
- **Started:** 2026-03-10T01:19:04Z
- **Completed:** 2026-03-10T01:26:00Z
- **Tasks:** 2 (Task 1: TDD RED+GREEN, Task 2: test infrastructure rewrite)
- **Files modified:** 15

## Accomplishments
- Replaced HTTP Basic Auth with session-based auth using Starlette SessionMiddleware (signed cookies)
- Added AuthRequired exception with HTMX-aware handler (303 redirect for normal, 204 + HX-Redirect for HTMX)
- Secured /dashboard/status endpoint with session auth (AUTH-08)
- Made session timeout configurable via SESSION_TIMEOUT_HOURS (default 168h / 7 days) (AUTH-07)
- Rewrote all test infrastructure: conftest.py dashboard_client fixture, test_auth.py with 11 tests across 6 test classes
- Updated 7 dashboard test files to use 303 redirects instead of 401 for unauthenticated access
- Zero HTTP Basic Auth references remain in src/ or tests/
- Full test suite: 282/282 passed

## Task Commits

Each task was committed atomically:

1. **Task 1 (RED): Failing tests for session-based auth** - `efba5e4` (test)
2. **Task 1 (GREEN) + Task 2: Session infrastructure and test rewrite** - `3d471d5` (feat)

_Note: Task 2 work (test infrastructure rewrite) was merged into Task 1's GREEN commit because updating all test files was a Rule 3 blocking requirement -- the new required session_secret_key field and 303 redirect behavior broke existing tests._

## Files Created/Modified
- `src/config.py` - Added session_secret_key (required) and session_timeout_hours (default 168) fields
- `src/backend/web/deps.py` - Complete rewrite: removed HTTP Basic Auth, added AuthRequired exception and session-based require_auth
- `src/backend/web/app.py` - Added SessionMiddleware and AuthRequired exception handler
- `src/backend/web/routes/dashboard.py` - Added Depends(require_auth) to status_router (AUTH-08)
- `.env.example` - Added SESSION_SECRET_KEY (required) and SESSION_TIMEOUT_HOURS (optional)
- `tests/test_auth.py` - Complete rewrite: 11 tests across 6 classes covering session auth, HTMX redirects, status auth, expiry, next URL validation
- `tests/conftest.py` - Removed base64 import, added session_secret_key to fixtures, rewrote dashboard_client to use session auth
- `tests/test_config.py` - Added session_secret_key to all Settings constructions and env file fixtures, added SESSION_SECRET_KEY to env example test
- `tests/test_dashboard_episodes.py` - Updated auth test: 401 -> 303 redirect to /login
- `tests/test_dashboard_hosts.py` - Removed base64/AUTH_HEADER, updated auth tests: 401 -> 303 redirect
- `tests/test_dashboard_presets.py` - Removed base64 import, updated auth tests: 401 -> 303 redirect
- `tests/test_dashboard_styles.py` - Removed base64/AUTH_HEADER, updated auth tests: 401 -> 303 redirect
- `tests/test_web_app.py` - Added session_secret_key to settings fixture
- `tests/test_podcast_service.py` - Added session_secret_key to settings fixture
- `tests/test_repositories.py` - Added session_secret_key to all Settings constructions

## Decisions Made
- Used AuthRequired exception + exception handler pattern (not Response return from dependency) to avoid FastAPI dependency injection limitation (Pitfall 5)
- Used test-only `/_test/login` route to establish session cookies in test fixtures, avoiding itsdangerous cookie manipulation complexity
- Merged Task 2 into Task 1's GREEN commit since all test infrastructure changes were blocking issues (Rule 3)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Added session_secret_key to all Settings constructions across test suite**
- **Found during:** Task 1 GREEN (full suite verification)
- **Issue:** New required session_secret_key field caused ValidationError in all test files constructing Settings without it
- **Fix:** Added session_secret_key to Settings calls in test_config.py, test_web_app.py, test_podcast_service.py, test_repositories.py, conftest.py (tmp_env_file and dashboard_settings fixtures)
- **Files modified:** tests/test_config.py, tests/test_web_app.py, tests/test_podcast_service.py, tests/test_repositories.py, tests/conftest.py
- **Verification:** All 282 tests pass
- **Committed in:** 3d471d5

**2. [Rule 3 - Blocking] Updated all dashboard auth tests from 401 to 303 redirect**
- **Found during:** Task 1 GREEN (full suite verification)
- **Issue:** 7 tests across 4 dashboard test files expected 401 for unauthenticated access; session auth now returns 303 redirect to /login
- **Fix:** Changed assertions from status_code == 401 to status_code == 303 with location header check, added follow_redirects=False to TestClient
- **Files modified:** tests/test_dashboard_episodes.py, tests/test_dashboard_hosts.py, tests/test_dashboard_presets.py, tests/test_dashboard_styles.py
- **Verification:** All 282 tests pass
- **Committed in:** 3d471d5

**3. [Rule 1 - Bug] Removed dead base64 imports and AUTH_HEADER constants**
- **Found during:** Task 1 GREEN (full suite verification)
- **Issue:** test_dashboard_hosts.py referenced base64 for AUTH_HEADER constant (removed import caused NameError)
- **Fix:** Removed unused base64 imports and AUTH_HEADER constants from test_dashboard_hosts.py, test_dashboard_styles.py, test_dashboard_presets.py, conftest.py
- **Files modified:** tests/test_dashboard_hosts.py, tests/test_dashboard_styles.py, tests/test_dashboard_presets.py, tests/conftest.py
- **Verification:** No NameError, all 282 tests pass
- **Committed in:** 3d471d5

---

**Total deviations:** 3 auto-fixed (2 blocking, 1 bug)
**Impact on plan:** All auto-fixes were direct consequences of replacing HTTP Basic Auth with session auth. No scope creep.

## Issues Encountered
None - all issues were expected consequences of the auth paradigm change and handled as deviations.

## User Setup Required

After updating, users must:
1. Generate a session secret key: `python -c "import secrets; print(secrets.token_hex(32))"`
2. Add `SESSION_SECRET_KEY=<generated-key>` to their `.env` file
3. The app will refuse to start until this is configured

## Next Phase Readiness
- Session infrastructure complete: SessionMiddleware active, require_auth checks session, AuthRequired handler works
- Plan 06-02 can build login/logout endpoints that set/clear `request.session["user"]`
- The `_ph = PasswordHasher()` and argon2 imports are preserved in deps.py for login endpoint password verification
- No login page exists yet -- unauthenticated requests redirect to /login which returns 404 until Plan 06-02

## Self-Check: PASSED

- All 15 modified files verified present on disk
- Commit efba5e4 (RED) verified in git log
- Commit 3d471d5 (GREEN) verified in git log
- Full test suite: 282/282 passed
- HTTPBasic grep in src/: 0 matches
- WWW-Authenticate grep in src/: 0 matches

---
*Phase: 06-authentication-overhaul*
*Completed: 2026-03-10*
