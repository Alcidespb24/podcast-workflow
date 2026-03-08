---
phase: 03-automation
plan: 02
subsystem: automation
tags: [watchdog, retry, backoff, debounce, threading]

requires:
  - phase: 01-foundation
    provides: "Exception hierarchy (ScriptGenerationError, TTSError)"
provides:
  - "DebouncedMarkdownHandler for .md file creation detection"
  - "retry_with_backoff with 429 awareness and exponential backoff"
affects: [03-automation]

tech-stack:
  added: [watchdog]
  patterns: [timer-based-debounce, 429-aware-retry, shutdown-event-interruption]

key-files:
  created:
    - src/backend/watcher/handler.py
    - src/application/retry.py
    - tests/test_watcher_handler.py
    - tests/test_retry.py
  modified:
    - src/exceptions.py
    - src/config.py

key-decisions:
  - "Handler uses threading.Timer with daemon=True for non-blocking debounce"
  - "Retry accepts individual params (not Settings) for testability and decoupling"
  - "RateLimitError without retry_after uses exponential backoff from current attempt number"

patterns-established:
  - "Timer-based debounce: cancel-and-restart pattern with lock-protected dict"
  - "Shutdown-aware waiting: use Event.wait(delay) instead of time.sleep for clean interruption"

requirements-completed: [AUTO-01, AUTO-02, AUTO-05, AUTO-06]

duration: 5min
completed: 2026-03-08
---

# Phase 3 Plan 2: Watcher Handler & Retry Module Summary

**Debounced watchdog handler filtering .md creation events and 429-aware retry with exponential backoff using shutdown-event interruption**

## Performance

- **Duration:** ~5 min
- **Started:** 2026-03-08T08:22:39Z
- **Completed:** 2026-03-08T08:28:00Z
- **Tasks:** 2
- **Files modified:** 6

## Accomplishments
- DebouncedMarkdownHandler filters .md-only creation events with timer-based debounce
- retry_with_backoff handles transient errors with exponential backoff, 429 without counting against limit
- 15 unit tests covering all handler and retry paths

## Task Commits

Each task was committed atomically:

1. **Task 1: Debounced watchdog handler** - `8f2df60` (feat)
2. **Task 2: 429-aware retry with backoff** - `82e56db` (feat)

_Both tasks followed TDD: RED (tests fail) -> GREEN (implementation passes)_

## Files Created/Modified
- `src/backend/watcher/__init__.py` - Package init
- `src/backend/watcher/handler.py` - DebouncedMarkdownHandler with timer-based debounce
- `src/application/retry.py` - retry_with_backoff with 429 awareness and exponential backoff
- `tests/test_watcher_handler.py` - 6 tests for .md filtering, debounce, cleanup
- `tests/test_retry.py` - 9 tests for success, retries, 429, backoff calc, shutdown
- `src/exceptions.py` - Added RateLimitError with retry_after attribute
- `src/config.py` - Added Phase 3 automation settings fields

## Decisions Made
- Handler uses threading.Timer with daemon=True for non-blocking debounce
- Retry function accepts individual parameters (not Settings object) for testability and decoupling
- RateLimitError without retry_after falls back to exponential backoff from current attempt number

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Added missing RateLimitError exception class**
- **Found during:** Task 1 (pre-requisite for Task 2)
- **Issue:** RateLimitError not yet in src/exceptions.py (Plan 01 dependency not yet executed)
- **Fix:** Added RateLimitError with retry_after attribute to exceptions.py
- **Files modified:** src/exceptions.py
- **Verification:** Import succeeds, tests pass
- **Committed in:** 8f2df60 (Task 1 commit)

**2. [Rule 3 - Blocking] Added Phase 3 config fields to Settings**
- **Found during:** Task 1 (pre-requisite for both tasks)
- **Issue:** Settings class missing watcher_debounce_seconds, max_retries, backoff fields
- **Fix:** Added all Phase 3 automation fields to Settings
- **Files modified:** src/config.py
- **Committed in:** 8f2df60 (Task 1 commit)

**3. [Rule 3 - Blocking] Installed watchdog dependency**
- **Found during:** Task 1 (test collection)
- **Issue:** watchdog package not installed
- **Fix:** pip install watchdog
- **Verification:** Import succeeds, tests pass

---

**Total deviations:** 3 auto-fixed (3 blocking)
**Impact on plan:** All auto-fixes necessary for prerequisites. No scope creep.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Both modules ready for integration by Plan 03 (job processor and watcher service)
- Handler provides on_file_ready callback for watcher service
- retry_with_backoff wraps API calls in job processor

---
*Phase: 03-automation*
*Completed: 2026-03-08*
