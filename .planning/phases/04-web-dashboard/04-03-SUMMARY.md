---
phase: 04-web-dashboard
plan: 03
subsystem: ui
tags: [fastapi, jinja2, htmx, pico-css, crud, audio-player, status-filter]

# Dependency graph
requires:
  - phase: 04-web-dashboard
    provides: Dashboard foundation (auth, session, base template, sidebar, toast system)
provides:
  - Preset CRUD with dropdown selectors for host/style assignment
  - Episode/job history view with status filtering and inline audio player
affects: []

# Tech tracking
tech-stack:
  added: []
  patterns: [HTMX status filter buttons, combined episode+job card list, dialog form with select dropdowns]

key-files:
  created:
    - src/backend/web/routes/api_presets.py
    - src/backend/web/templates/partials/presets/form.html
    - src/backend/web/templates/partials/presets/row.html
    - src/backend/web/templates/partials/presets/row_list.html
    - src/backend/web/templates/partials/episodes/card.html
    - src/backend/web/templates/partials/episodes/filters.html
    - tests/test_dashboard_presets.py
    - tests/test_dashboard_episodes.py
  modified:
    - src/backend/web/routes/dashboard.py
    - src/backend/web/templates/partials/presets/list.html
    - src/backend/web/templates/partials/episodes/list.html
    - src/backend/web/static/app.css
    - src/backend/web/app.py

key-decisions:
  - "Combined episode+job view builds a unified display list sorted by date descending"
  - "Status filter uses query parameter (status=complete|failed|in_progress) with HTMX partial swap"
  - "Preset form uses dialog element with hx-on::after-request to auto-close on success"
  - "Date format uses %b %d (not %-d) for Windows cross-platform compatibility"

patterns-established:
  - "CRUD route module pattern: separate api_{entity}.py with _render_list helper for consistent toast+list returns"
  - "Status filter pattern: filter bar buttons with hx-get and query params targeting #list container"
  - "Card-based history: article element per item with conditional rendering based on item type"

requirements-completed: [DASH-03, DASH-04]

# Metrics
duration: 5min
completed: 2026-03-08
---

# Phase 4 Plan 3: Preset CRUD and Episode History Summary

**Preset CRUD with host/style dropdown selectors and combined episode/job history view with HTMX status filtering and HTML5 audio player**

## Performance

- **Duration:** 5 min
- **Started:** 2026-03-08T22:30:15Z
- **Completed:** 2026-03-08T22:35:11Z
- **Tasks:** 2
- **Files modified:** 13

## Accomplishments
- Preset management with create/edit/delete, dropdown selectors populated from Host and Style repositories, and resolved name display in table
- Episode/job history as card-based view combining completed episodes and active/failed jobs, sorted by date descending
- HTML5 audio player on completed episode cards with preload=none for bandwidth efficiency
- Status filter buttons (All/Complete/Failed/In Progress) swapping card list via HTMX
- 32 integration tests covering preset CRUD, episode listing, status filtering, audio presence, and auth

## Task Commits

Each task was committed atomically:

1. **Task 1: Preset CRUD routes, templates with dropdown selectors, and tests** - `87fc22f` (feat)
2. **Task 2: Episode/job history view with status filtering and audio player** - `6076a69` (feat)

## Files Created/Modified
- `src/backend/web/routes/api_presets.py` - Preset CRUD endpoints (GET new/edit, POST, PUT, DELETE) with toast feedback
- `src/backend/web/routes/dashboard.py` - Updated presets page with resolved names, episodes page with combined episode+job listing and status filter
- `src/backend/web/templates/partials/presets/list.html` - Preset table with "New Preset" button
- `src/backend/web/templates/partials/presets/row_list.html` - Inner table content swapped on CRUD operations
- `src/backend/web/templates/partials/presets/row.html` - Table row with edit/delete action buttons
- `src/backend/web/templates/partials/presets/form.html` - Dialog form with host/style select dropdowns
- `src/backend/web/templates/partials/episodes/list.html` - Episode list with filter bar and card loop
- `src/backend/web/templates/partials/episodes/card.html` - Episode/job card with conditional audio player, error display, and status badges
- `src/backend/web/templates/partials/episodes/filters.html` - Status filter button bar with HTMX targeting
- `src/backend/web/static/app.css` - Episode card, status badge, and filter bar styles
- `src/backend/web/app.py` - Registered api_presets router
- `tests/test_dashboard_presets.py` - 21 integration tests for preset CRUD
- `tests/test_dashboard_episodes.py` - 11 integration tests for episode/job history

## Decisions Made
- Combined episode+job view builds a unified list of dicts with common fields (type, title, date, status) plus the original object, sorted by date descending
- Status filter uses query parameter with HTMX partial swap on #episode-list div
- Preset form uses dialog element with auto-close via hx-on::after-request event
- Date format uses `%b %d` (not `%-d`) for Windows cross-platform compatibility

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Windows-incompatible strftime format**
- **Found during:** Task 2 (episode card template)
- **Issue:** `%-d` format specifier (zero-padding removal) not supported on Windows
- **Fix:** Changed to `%d` which works cross-platform
- **Files modified:** src/backend/web/templates/partials/episodes/card.html
- **Verification:** All 11 episode tests pass on Windows
- **Committed in:** 6076a69 (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (1 bug)
**Impact on plan:** Minor format fix for Windows compatibility. No scope creep.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Phase 4 complete -- all 3 plans executed (dashboard foundation, host/style CRUD, preset CRUD + episodes)
- Full dashboard with HTMX navigation, CRUD for all entities, and episode history with audio playback

---
*Phase: 04-web-dashboard*
*Completed: 2026-03-08*
