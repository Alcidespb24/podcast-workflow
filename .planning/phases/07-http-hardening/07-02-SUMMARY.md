---
phase: 07-http-hardening
plan: 02
subsystem: security
tags: [csrf, htmx, session-tokens, fastapi-dependencies]

requires:
  - phase: 06-auth-ui
    provides: Session-based auth, login/logout routes, base.html template
provides:
  - CSRFError exception class and require_csrf dependency
  - ensure_csrf_token helper for template routes
  - CSRF meta tag in base.html and login.html
  - JavaScript CSRF token injection via hx-headers
  - CSRF exception handler (plain 403 + HTMX toast)
affects: [08-production-readiness]

tech-stack:
  added: []
  patterns: [header-based CSRF with hx-headers, safe-method exemption in dependency]

key-files:
  created:
    - tests/test_csrf.py
  modified:
    - src/backend/web/deps.py
    - src/backend/web/app.py
    - src/backend/web/routes/auth.py
    - src/backend/web/routes/api_hosts.py
    - src/backend/web/routes/api_styles.py
    - src/backend/web/routes/api_presets.py
    - src/backend/web/templates/base.html
    - src/backend/web/templates/login.html
    - src/backend/web/static/app.js
    - src/backend/web/routes/dashboard.py
    - tests/test_auth.py
    - tests/conftest.py

key-decisions:
  - "require_csrf skips GET/HEAD/OPTIONS methods so it can be applied at router level safely"
  - "Login POST validates CSRF inline (not via Depends) for custom error handling"
  - "Logout converted from form POST to hx-post with hx-confirm for CSRF compatibility via hx-headers"
  - "CSRF token regenerated on successful login to prevent session fixation"

patterns-established:
  - "Header-based CSRF: meta tag in HTML head, JS reads and sets hx-headers on body, require_csrf dependency validates"
  - "Safe-method exemption: router-level dependencies skip GET/HEAD/OPTIONS automatically"

requirements-completed: [HTTP-04]

duration: 5min
completed: 2026-03-10
---

# Phase 7 Plan 2: CSRF Protection Summary

**Header-based CSRF protection on all POST/PUT/DELETE endpoints using session tokens, meta tags, and HTMX hx-headers injection**

## Performance

- **Duration:** 5 min
- **Started:** 2026-03-10T03:42:53Z
- **Completed:** 2026-03-10T03:47:44Z
- **Tasks:** 2
- **Files modified:** 12

## Accomplishments
- All POST/PUT/DELETE endpoints reject requests without valid X-CSRF-Token header (403)
- CSRF tokens delivered via meta tag, read by JavaScript, and injected as hx-headers on body
- Login generates token on GET, regenerates on successful POST (session fixation prevention)
- Logout converted to HTMX hx-post with hx-confirm for CSRF header compatibility
- 315/315 tests pass with zero regressions

## Task Commits

Each task was committed atomically:

1. **Task 1: CSRF dependency, exception handler, token generation, and tests** - `8768f9a` (test: TDD RED) + `0121c8c` (feat: TDD GREEN)
2. **Task 2: Wire CSRF to API routers, update templates and JS** - `92c0faa` (feat)
3. **Fix: Update test fixtures with CSRF token support** - `2ed7667` (fix: deviation Rule 1)

## Files Created/Modified
- `src/backend/web/deps.py` - CSRFError exception, require_csrf dependency, ensure_csrf_token helper
- `src/backend/web/app.py` - CSRF exception handler (403 plain + HTMX toast)
- `src/backend/web/routes/auth.py` - Login CSRF generation/validation/regeneration, logout CSRF check
- `src/backend/web/routes/api_hosts.py` - Added Depends(require_csrf) to router
- `src/backend/web/routes/api_styles.py` - Added Depends(require_csrf) to router
- `src/backend/web/routes/api_presets.py` - Added Depends(require_csrf) to router
- `src/backend/web/routes/dashboard.py` - Pass csrf_token to template context via ensure_csrf_token
- `src/backend/web/templates/base.html` - CSRF meta tag, logout converted to hx-post
- `src/backend/web/templates/login.html` - CSRF meta tag, added app.js script
- `src/backend/web/static/app.js` - CSRF token injection IIFE (reads meta, sets hx-headers)
- `tests/test_csrf.py` - 9 integration tests for CSRF protection
- `tests/test_auth.py` - Updated all POST tests to include CSRF tokens
- `tests/conftest.py` - Updated dashboard_client fixture with CSRF token support

## Decisions Made
- require_csrf skips GET/HEAD/OPTIONS so it can be safely applied at router level (routers have both GET and POST routes)
- Login POST validates CSRF inline rather than via Depends(require_csrf) since login has custom error handling
- Logout converted from plain form POST to hx-post with hx-confirm attribute, so body-level hx-headers sends CSRF token automatically
- CSRF token regenerated on successful login for session fixation prevention

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed existing tests broken by CSRF enforcement**
- **Found during:** Task 2 verification
- **Issue:** Existing test_auth.py and conftest.py dashboard_client fixture did not include CSRF tokens, causing 403s on all POST/PUT/DELETE tests
- **Fix:** Updated conftest dashboard_client to set csrf_token in session and inject X-CSRF-Token header by default; updated test_auth.py login/logout tests to include CSRF tokens
- **Files modified:** tests/conftest.py, tests/test_auth.py
- **Verification:** 315/315 tests pass
- **Committed in:** 2ed7667

---

**Total deviations:** 1 auto-fixed (1 bug fix)
**Impact on plan:** Necessary to prevent test regressions from CSRF enforcement. No scope creep.

## Issues Encountered
None beyond the expected test fixture updates.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- All HTTP hardening security measures now in place (rate limiting, security headers, CORS, CSRF)
- Ready for Phase 8 production readiness

---
*Phase: 07-http-hardening*
*Completed: 2026-03-10*
