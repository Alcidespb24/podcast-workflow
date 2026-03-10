---
phase: 06-authentication-overhaul
plan: 02
subsystem: auth
tags: [login-page, logout, htmx-form, session-auth, pico-css, branded-login]

# Dependency graph
requires:
  - phase: 06-authentication-overhaul
    provides: SessionMiddleware, AuthRequired exception handler, session-based require_auth, PasswordHasher in deps.py
provides:
  - Branded login page with HTMX form submission and inline error feedback
  - Login endpoint with session creation, open redirect prevention, and next-URL preservation
  - Logout endpoint with session invalidation and redirect to login
  - Root URL (/) redirect based on auth state
  - Sidebar logout button with browser confirmation dialog
affects: [07-http-hardening]

# Tech tracking
tech-stack:
  added: [itsdangerous]
  patterns: [htmx-inline-error-swap, 204-hx-redirect-login, standalone-login-template, post-form-logout-with-confirm]

key-files:
  created:
    - src/backend/web/routes/auth.py
    - src/backend/web/templates/login.html
  modified:
    - src/backend/web/app.py
    - src/backend/web/static/app.css
    - src/backend/web/templates/base.html
    - tests/test_auth.py
    - pyproject.toml

key-decisions:
  - "Login form uses HTMX hx-post with hx-target=#login-error for inline error display without page reload"
  - "POST /login returns 204 + HX-Redirect header on success (not 3xx, which HTMX ignores)"
  - "Open redirect prevention: only /dashboard/* paths accepted for ?next= parameter"
  - "Standalone login.html template (not extending base.html) for clean unauthenticated experience"

patterns-established:
  - "Login error pattern: hx-target=#login-error with hx-swap=innerHTML returns small HTML error fragment"
  - "Logout pattern: POST form with onsubmit=confirm() in sidebar, returns 303 redirect to /login?logged_out=1"
  - "Root redirect: GET / checks session, redirects to /dashboard/episodes or /login"

requirements-completed: [AUTH-05, AUTH-06]

# Metrics
duration: 43min
completed: 2026-03-10
---

# Phase 6 Plan 02: Login/Logout UI Summary

**Branded login page with HTMX form, inline error feedback, session-based login/logout endpoints, sidebar logout button with confirmation dialog, and root URL redirect**

## Performance

- **Duration:** 43 min (including human verification checkpoint)
- **Started:** 2026-03-10T01:30:49Z
- **Completed:** 2026-03-10T02:30:00Z
- **Tasks:** 3 (Task 1: TDD RED+GREEN, Task 2: sidebar + verification, Task 3: human verification)
- **Files modified:** 7

## Accomplishments
- Created branded login page with podcast name/cover, dark theme, Pico CSS, and HTMX form submission
- Implemented login endpoint: validates credentials with Argon2id, sets session cookie, redirects via HX-Redirect with next-URL support
- Implemented logout endpoint: clears session, redirects to login page with "logged out" message
- Added open redirect prevention (only /dashboard/* paths allowed in ?next= parameter)
- Inline error display for invalid credentials without page reload (HTMX swap)
- Root URL (/) redirects to /login or /dashboard/episodes based on auth state
- Added logout button with browser confirmation dialog in sidebar on all dashboard pages
- All 294 tests passing with zero regressions

## Task Commits

Each task was committed atomically:

1. **Task 1 (RED): Failing tests for login/logout/root-redirect** - `04f6688` (test)
2. **Task 1 (GREEN): Auth routes, login template, CSS, router wiring** - `30562aa` (feat)
3. **Task 2: Logout button in sidebar + full verification** - `d87f474` (feat)
4. **Task 3: Human verification of complete login/logout flow** - approved (checkpoint)

## Files Created/Modified
- `src/backend/web/routes/auth.py` - New file: login/logout endpoints, root redirect, _validate_next_url helper
- `src/backend/web/templates/login.html` - New file: standalone branded login page with HTMX form, error div, logged-out message
- `src/backend/web/app.py` - Wired auth_router into app (include_router before static mounts)
- `src/backend/web/static/app.css` - Added login page styles (.login-container, .login-hero, .login-alert)
- `src/backend/web/templates/base.html` - Added logout form with confirmation dialog at bottom of sidebar
- `tests/test_auth.py` - Added TestLoginPage, TestLoginSubmission, TestLogout, TestRootRedirect, TestSidebarLogout test classes
- `pyproject.toml` - Added itsdangerous to project dependencies

## Decisions Made
- Login form uses HTMX hx-post with hx-target=#login-error for inline error display without page reload
- POST /login returns 204 + HX-Redirect header on success (HTMX ignores headers on 3xx responses)
- Open redirect prevention: only /dashboard/* paths accepted for ?next= parameter, all others fall back to /dashboard/episodes
- Standalone login.html template (not extending base.html) for clean unauthenticated experience without sidebar

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Added itsdangerous to pyproject.toml dependencies**
- **Found during:** Task 2 (full test suite verification)
- **Issue:** SessionMiddleware from Starlette requires itsdangerous for cookie signing, but it was not listed in pyproject.toml dependencies
- **Fix:** Added itsdangerous to the project dependencies in pyproject.toml
- **Files modified:** pyproject.toml
- **Verification:** All 294 tests pass, no import errors
- **Committed in:** 3f87707

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** Missing transitive dependency that was required at runtime. No scope creep.

## Issues Encountered
None - all planned work executed successfully. The itsdangerous dependency was a missing transitive dependency, handled as a deviation.

## User Setup Required
None - all setup was completed in Plan 06-01 (SESSION_SECRET_KEY in .env).

## Next Phase Readiness
- Authentication overhaul complete: branded login page, session-based auth, logout flow all working
- Phase 7 (HTTP Hardening) can build on this: rate limiting on /login endpoint, CSRF tokens for POST/PUT/DELETE, security headers
- The login endpoint at POST /login is the primary target for rate limiting (HTTP-01)
- All HTMX POST operations (host/style/preset CRUD + login + logout) need CSRF token integration (HTTP-04)

## Self-Check: PASSED

- All 7 modified files verified present on disk
- Commit 04f6688 (RED) verified in git log
- Commit 30562aa (GREEN) verified in git log
- Commit d87f474 (Task 2) verified in git log
- Commit 3f87707 (itsdangerous fix) verified in git log
- Full test suite: 294/294 passed

---
*Phase: 06-authentication-overhaul*
*Completed: 2026-03-10*
