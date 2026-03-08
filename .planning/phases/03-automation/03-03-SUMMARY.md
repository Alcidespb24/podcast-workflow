---
phase: 03-automation
plan: 03
subsystem: automation
tags: [watchdog, threading, fastapi-lifespan, job-processing, retry, cli]

requires:
  - phase: 03-automation (plan 01)
    provides: Job/Preset/JobState domain models, JobRepository, PresetRepository
  - phase: 03-automation (plan 02)
    provides: DebouncedMarkdownHandler, retry_with_backoff

provides:
  - JobProcessor: sequential pipeline executor with retry and state tracking
  - WatcherService: manages Observer + JobProcessor lifecycle
  - FastAPI lifespan integration for auto-start/stop watcher
  - Standalone CLI for running watcher without web server
  - python -m src watch entry point

affects: [04-dashboard]

tech-stack:
  added: []
  patterns: [daemon-thread processor, lifespan context manager, session-per-retry]

key-files:
  created:
    - src/application/job_processor.py
    - src/backend/watcher/service.py
    - src/backend/cli/__init__.py
    - src/backend/cli/watch.py
    - src/__main__.py
  modified:
    - src/backend/web/app.py

key-decisions:
  - "State transitions walk full path PROCESSING->ENCODING->PUBLISHING->COMPLETE (state machine enforces valid_transitions)"
  - "Fresh session per retry attempt to avoid stale SQLAlchemy state"
  - "TYPE_CHECKING guard for WatcherService import in app.py to avoid circular imports"

patterns-established:
  - "Daemon thread pattern: JobProcessor.run() called in daemon thread, controlled via shutdown_event"
  - "Lifespan pattern: FastAPI asynccontextmanager for watcher start/stop"

requirements-completed: [AUTO-01, AUTO-02, AUTO-03, AUTO-04, AUTO-05, AUTO-06]

duration: 5min
completed: 2026-03-08
---

# Phase 03 Plan 03: Integration and Wiring Summary

**Sequential job processor with retry/state tracking, watcher service lifecycle, FastAPI lifespan integration, and standalone CLI entry point**

## Performance

- **Duration:** 5 min
- **Started:** 2026-03-08T13:38:34Z
- **Completed:** 2026-03-08T13:43:34Z
- **Tasks:** 2
- **Files modified:** 6

## Accomplishments
- JobProcessor polls pending jobs, recovers interrupted jobs on startup, processes with retry_with_backoff, tracks state machine transitions
- WatcherService manages watchdog Observer and JobProcessor in daemon thread with graceful shutdown
- FastAPI lifespan auto-starts/stops watcher when app boots
- Standalone CLI runs watcher without web server via `python -m src watch`

## Task Commits

Each task was committed atomically:

1. **Task 1: JobProcessor** - `2ee1b13` (feat)
2. **Task 2: WatcherService, FastAPI lifespan, CLI** - `7e9a830` (feat)

## Files Created/Modified
- `src/application/job_processor.py` - Sequential job processor with retry, state tracking, recovery
- `src/backend/watcher/service.py` - WatcherService managing Observer + JobProcessor lifecycle
- `src/backend/web/app.py` - Added lifespan context manager and watcher_service parameter
- `src/backend/cli/__init__.py` - CLI package init
- `src/backend/cli/watch.py` - Standalone watcher CLI entry point
- `src/__main__.py` - Package entry point for `python -m src watch`

## Decisions Made
- State transitions must walk full path (PROCESSING->ENCODING->PUBLISHING->COMPLETE) because valid_transitions() on JobState only allows adjacent transitions. Plan suggested PROCESSING->COMPLETE directly but the domain model disallows it.
- Fresh SQLAlchemy session per retry attempt to avoid stale ORM state after rollback.
- Used TYPE_CHECKING guard for WatcherService import in app.py to prevent circular imports.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] State machine requires full transition path, not PROCESSING->COMPLETE**
- **Found during:** Task 1 (JobProcessor)
- **Issue:** Plan specified PROCESSING->COMPLETE on success, but JobState.valid_transitions() only allows PROCESSING->ENCODING, ENCODING->PUBLISHING, PUBLISHING->COMPLETE
- **Fix:** Walk through all intermediate states after generate_podcast returns
- **Files modified:** src/application/job_processor.py
- **Verification:** Import succeeds, state transitions would be valid at runtime
- **Committed in:** 2ee1b13

---

**Total deviations:** 1 auto-fixed (1 bug)
**Impact on plan:** Essential fix for correctness. No scope creep.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Full automation pipeline wired end-to-end: file drop -> debounce -> enqueue -> process -> podcast
- Ready for Phase 4 dashboard work
- Manual end-to-end test recommended with real preset configuration

---
*Phase: 03-automation*
*Completed: 2026-03-08*
