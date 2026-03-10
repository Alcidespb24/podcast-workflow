---
phase: 08-path-validation
plan: 02
subsystem: security
tags: [path-traversal, htmx-inline-errors, preset-validation, watcher-guard]

# Dependency graph
requires:
  - phase: 08-path-validation
    provides: validate_path_within() function, PathTraversalError exception, VAULT_BASE_DIR config
provides:
  - Path validation on preset create/update routes (422 on traversal)
  - Inline form error display for path validation failures
  - Warning badge on preset cards with out-of-bounds paths
  - Watcher skip logic for invalid preset folder paths
  - Reader and writer path validation before filesystem I/O
  - vault_base_dir flow through podcast_service and job_processor
affects: []

# Tech tracking
tech-stack:
  added: []
  patterns: [422+PlainTextResponse for HTMX inline errors, event.detail.successful dialog close guard, path_valid badge in template context]

key-files:
  created: []
  modified:
    - src/backend/web/routes/api_presets.py
    - src/backend/web/templates/partials/presets/form.html
    - src/backend/web/templates/partials/presets/row.html
    - src/backend/watcher/service.py
    - src/infrastructure/reader.py
    - src/infrastructure/obsidian_writer.py
    - src/application/podcast_service.py
    - src/application/job_processor.py
    - tests/test_dashboard_presets.py
    - tests/test_path_validation.py

key-decisions:
  - "422 PlainTextResponse for path errors with JS-based inline error injection (no HTMX extensions needed)"
  - "Dialog close guarded by event.detail.successful check so 422 keeps dialog open"
  - "vault_base_dir parameter is optional (None) in reader/writer for backward compatibility"

patterns-established:
  - "Inline form errors: return 422 PlainTextResponse, inject via hx-on::after-request JS handler"
  - "Warning badge pattern: validate in _render_preset_list, pass path_valid to template context"

requirements-completed: [PATH-01, PATH-02]

# Metrics
duration: 5min
completed: 2026-03-10
---

# Phase 8 Plan 02: Path Validation Wiring Summary

**Path traversal validation wired into all 6 unprotected filesystem operations with 422 inline form errors, warning badges, and watcher skip guards**

## Performance

- **Duration:** 5 min
- **Started:** 2026-03-10T06:06:03Z
- **Completed:** 2026-03-10T06:11:11Z
- **Tasks:** 2
- **Files modified:** 10

## Accomplishments
- Preset create/update reject traversal paths with 422 and generic "Path must be within the vault directory." message
- Dialog stays open on validation error, inline error injected via JS; closes only on success
- Warning badge on preset cards with out-of-bounds paths; app starts normally with legacy invalid presets
- Watcher validates and skips invalid presets with WARNING log before scheduling
- Reader and writer validate paths before any filesystem I/O
- Pipeline callers (podcast_service, job_processor) pass vault_base_dir through to reader/writer
- 343 tests pass (1 skipped), zero regressions

## Task Commits

Each task was committed atomically:

1. **Task 1: Preset route validation, inline form errors, and warning badge** - `eb24d45` (test: RED), `72eeb32` (feat: GREEN)
2. **Task 2: Wire validation into watcher, reader, writer, and pipeline callers** - `9519bc7` (test: RED), `6c33162` (feat: GREEN)

_TDD tasks have RED/GREEN commits. No refactor phase needed._

## Files Created/Modified
- `src/backend/web/routes/api_presets.py` - Path validation on create/update, path_valid in preset list context
- `src/backend/web/templates/partials/presets/form.html` - Vault-relative placeholder, inline error element, dialog close guard
- `src/backend/web/templates/partials/presets/row.html` - Warning badge for invalid preset paths
- `src/backend/watcher/service.py` - validate_path_within before os.path.isdir check
- `src/infrastructure/reader.py` - Optional vault_base_dir parameter with path validation
- `src/infrastructure/obsidian_writer.py` - Optional vault_base_dir parameter with path validation
- `src/application/podcast_service.py` - Passes vault_base_dir to reader and writer
- `src/application/job_processor.py` - Passes vault_base_dir to reader in cleanup
- `tests/test_dashboard_presets.py` - 7 new tests, updated existing tests for vault_base_dir paths
- `tests/test_path_validation.py` - 8 new integration tests for reader, writer, watcher validation

## Decisions Made
- Used 422 PlainTextResponse for path validation errors with JS-based error injection (avoids HTMX response-targets extension dependency)
- Dialog close uses `event.detail.successful` guard so 422 responses keep dialog open
- vault_base_dir is optional (None) in reader/writer signatures for backward compatibility with any callers that lack vault context

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Updated test_update_preset_returns_404_for_missing to use valid path**
- **Found during:** Task 1 (GREEN phase)
- **Issue:** Existing test used `/vault/x` as folder_path which now fails path validation (422) before reaching 404 preset-not-found check
- **Fix:** Changed test to use path under dashboard_settings.vault_base_dir
- **Files modified:** tests/test_dashboard_presets.py
- **Verification:** All 28 preset tests pass
- **Committed in:** 72eeb32 (Task 1 GREEN commit)

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** Required fix for pre-existing test using hardcoded path. No scope creep.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required. VAULT_BASE_DIR was already added in Plan 01.

## Next Phase Readiness
- All 6 unprotected filesystem operations are now gated by validate_path_within
- Phase 8 (Path Validation) is fully complete
- v1.1 Security Hardening milestone is fully complete

---
*Phase: 08-path-validation*
*Completed: 2026-03-10*
