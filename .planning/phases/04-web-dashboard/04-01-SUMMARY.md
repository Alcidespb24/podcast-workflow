---
phase: 04-web-dashboard
plan: 01
subsystem: ui
tags: [fastapi, jinja2, htmx, pico-css, http-basic-auth, sqlalchemy]

# Dependency graph
requires:
  - phase: 03-automation
    provides: WatcherService, JobRepository, PresetRepository, app.py factory
provides:
  - deps.py with get_db and require_auth dependencies
  - base.html with sidebar layout, Pico CSS dark mode, HTMX navigation
  - Dashboard app factory wiring (templates, static files, session_factory)
  - Toast notification system (CSS + JS + partial template)
  - PresetRepository.update() and JobRepository.get_all() methods
affects: [04-02-PLAN, 04-03-PLAN]

# Tech tracking
tech-stack:
  added: [jinja2, htmx, pico-css]
  patterns: [HTMX partial/full-page detection, HTTP Basic Auth dependency, sidebar status polling]

key-files:
  created:
    - src/backend/web/deps.py
    - src/backend/web/routes/dashboard.py
    - src/backend/web/templates/base.html
    - src/backend/web/templates/partials/sidebar_status.html
    - src/backend/web/templates/partials/toast.html
    - src/backend/web/static/app.css
    - src/backend/web/static/app.js
  modified:
    - src/config.py
    - src/infrastructure/database/repositories.py
    - src/backend/web/app.py
    - tests/conftest.py

key-decisions:
  - "Status endpoint manages its own session (no Depends(get_db)) to work when session_factory is None"
  - "Status endpoint has no auth -- accessed via HTMX polling from already-authenticated page"
  - "DRY page routing with _render_page helper and HX-Request header detection for partial vs full responses"

patterns-established:
  - "HTMX navigation: sidebar links use hx-get + hx-push-url for SPA-like partial swaps"
  - "Full vs partial rendering: check HX-Request header to return partial or base.html wrapper"
  - "Toast OOB swap: server returns toast partial with hx-swap-oob, JS auto-dismisses after 3s"

requirements-completed: [DASH-05, DASH-06]

# Metrics
duration: 4min
completed: 2026-03-08
---

# Phase 4 Plan 1: Dashboard Foundation Summary

**FastAPI dashboard with HTTP Basic Auth, Pico CSS dark-mode sidebar layout, HTMX navigation, and toast notification system**

## Performance

- **Duration:** 4 min
- **Started:** 2026-03-08T22:22:28Z
- **Completed:** 2026-03-08T22:26:44Z
- **Tasks:** 2
- **Files modified:** 16

## Accomplishments
- HTTP Basic Auth dependency enforces credentials on all dashboard routes (401 without, 200 with)
- Base HTML template with sticky sidebar navigation (Episodes, Hosts, Styles, Presets) and HTMX-powered partial swaps
- Sidebar status indicator polls /dashboard/status every 30s showing watcher state, pending job count, and last episode time
- Toast notification system with CSS animations and auto-dismiss JS
- PresetRepository.update() and JobRepository.get_all() repository methods added for dashboard CRUD

## Task Commits

Each task was committed atomically:

1. **Task 1: Backend infrastructure** - `b94a301` (feat)
2. **Task 2: Base template, static assets, sidebar** - `ddae4b9` (feat)

## Files Created/Modified
- `src/backend/web/deps.py` - get_db session dependency and require_auth Basic Auth dependency
- `src/backend/web/routes/dashboard.py` - Dashboard router with auth, page endpoints, status polling
- `src/backend/web/templates/base.html` - Full HTML5 layout with Pico CSS, HTMX, sidebar, toast container
- `src/backend/web/templates/partials/sidebar_status.html` - Watcher status and job count partial
- `src/backend/web/templates/partials/toast.html` - Reusable toast notification with OOB swap
- `src/backend/web/templates/partials/episodes/list.html` - Placeholder episodes partial
- `src/backend/web/templates/partials/hosts/list.html` - Placeholder hosts partial
- `src/backend/web/templates/partials/styles/list.html` - Placeholder styles partial
- `src/backend/web/templates/partials/presets/list.html` - Placeholder presets partial
- `src/backend/web/static/app.css` - Dashboard grid layout, sidebar styling, toast animations
- `src/backend/web/static/app.js` - Toast auto-dismiss and modal close event handling
- `src/config.py` - Added dashboard_username, REDACTED_FIELD, dashboard_host settings
- `src/infrastructure/database/repositories.py` - Added PresetRepository.update() and JobRepository.get_all()
- `src/backend/web/app.py` - Extended create_app with session_factory, templates, static files, dashboard router
- `tests/conftest.py` - Added dashboard_settings, session_factory, dashboard_client fixtures

## Decisions Made
- Status endpoint uses its own session management instead of Depends(get_db) to handle cases where session_factory is None (e.g., tests without database)
- Status endpoint has no auth requirement since it is called by HTMX polling from an already-authenticated page
- Used a DRY _render_page helper with HX-Request header detection for partial vs full-page rendering

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Status endpoint NoneType error when session_factory is None**
- **Found during:** Task 2 (status endpoint integration)
- **Issue:** Using Depends(get_db) on the status endpoint fails when session_factory is None because get_db calls session_factory() unconditionally
- **Fix:** Status endpoint manages its own session lifecycle, checking if session_factory is available before creating a session
- **Files modified:** src/backend/web/routes/dashboard.py
- **Verification:** Status endpoint returns 200 with and without session_factory
- **Committed in:** ddae4b9 (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (1 bug)
**Impact on plan:** Necessary fix for correctness. No scope creep.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Dashboard foundation ready for Plan 02 (Host and Style CRUD)
- All placeholder partials in place for replacement
- Auth, session dependency, and toast system ready for CRUD forms

---
*Phase: 04-web-dashboard*
*Completed: 2026-03-08*
