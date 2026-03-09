---
phase: 05-secrets-and-configuration-foundation
plan: 01
subsystem: auth
tags: [argon2, pydantic-settings, password-hashing, env-config]

# Dependency graph
requires:
  - phase: 04-web-dashboard
    provides: Settings class with REDACTED_FIELD, HTTP Basic Auth in deps.py
provides:
  - Settings class with REDACTED_FIELD_hash (Argon2id validated)
  - load_settings() function with friendly error checklist
  - hash_password CLI tool for generating Argon2id hashes
  - .env.example documenting all environment variables
  - Argon2id password verification in require_auth dependency
affects: [05-02-auth-integration, 06-authentication-overhaul]

# Tech tracking
tech-stack:
  added: [argon2-cffi]
  patterns: [load_settings-startup-validation, argon2id-hash-field-validator]

key-files:
  created:
    - src/hash_password.py
    - .env.example
  modified:
    - src/config.py
    - pyproject.toml
    - run_dashboard.py
    - src/backend/cli/watch.py
    - src/backend/web/deps.py
    - tests/conftest.py
    - tests/test_config.py
    - tests/test_web_app.py
    - tests/test_podcast_service.py
    - tests/test_repositories.py

key-decisions:
  - "Updated deps.py require_auth to use Argon2id verification inline (was blocking tests, Plan 05-02 will refine further)"
  - "Used module-level TEST_HASH = PasswordHasher().hash('testpass') in test files for Argon2id fixture consistency"

patterns-established:
  - "load_settings() pattern: entry points call load_settings() instead of raw Settings() for friendly startup errors"
  - "Argon2id hash validator: field_validator checks $argon2id$ prefix on REDACTED_FIELD_hash"

requirements-completed: [SEC-01, SEC-02, AUTH-02, AUTH-03]

# Metrics
duration: 4min
completed: 2026-03-09
---

# Phase 5 Plan 01: Config Foundation Summary

**Argon2id hash field with startup validation, hash_password CLI tool, .env.example, and load_settings() error checklist across all entry points**

## Performance

- **Duration:** 4 min
- **Started:** 2026-03-09T21:17:05Z
- **Completed:** 2026-03-09T21:21:54Z
- **Tasks:** 2
- **Files modified:** 12

## Accomplishments
- Replaced plaintext REDACTED_FIELD with required REDACTED_FIELD_hash field validated as Argon2id
- Created load_settings() function that prints UPPERCASE env var error checklist and exits on invalid config
- Built src/hash_password.py CLI tool with interactive double-prompt and formatted .env output
- Created .env.example documenting all 24 required and optional environment variables
- Updated both entry points (run_dashboard.py, watch.py) to use load_settings()
- Updated deps.py require_auth to verify passwords against Argon2id hash
- Migrated all test fixtures across 5 test files to use REDACTED_FIELD_hash
- Full 271-test suite passes

## Task Commits

Each task was committed atomically:

1. **Task 1 (RED): Failing tests for hash validation and startup checklist** - `59f71ef` (test)
2. **Task 1 (GREEN): Settings hash field, validator, load_settings(), .env.example** - `c113a2a` (feat)
3. **Task 2: hash_password CLI, entry point updates, deps.py fix, all test fixtures** - `db1a252` (feat)

## Files Created/Modified
- `src/config.py` - Settings with REDACTED_FIELD_hash, field_validator, load_settings()
- `src/hash_password.py` - CLI tool for generating Argon2id password hashes
- `.env.example` - Documents all 24 Settings fields with placeholders and commented defaults
- `pyproject.toml` - Added argon2-cffi>=25.1.0 dependency
- `run_dashboard.py` - Uses load_settings() instead of raw Settings()
- `src/backend/cli/watch.py` - Uses load_settings() instead of raw Settings()
- `src/backend/web/deps.py` - require_auth verifies password against Argon2id hash
- `tests/conftest.py` - Updated tmp_env_file and dashboard_settings fixtures with TEST_HASH
- `tests/test_config.py` - New tests for hash validation, startup checklist, env.example coverage
- `tests/test_web_app.py` - Added REDACTED_FIELD_hash to settings fixture
- `tests/test_podcast_service.py` - Added REDACTED_FIELD_hash to settings fixture
- `tests/test_repositories.py` - Added REDACTED_FIELD_hash to all Settings() constructions

## Decisions Made
- Updated deps.py require_auth to use Argon2id verification immediately rather than leaving broken code for Plan 05-02 -- this was necessary because removing REDACTED_FIELD would crash all auth-dependent tests
- Used module-level TEST_HASH constants in test files rather than a shared conftest fixture, for explicit locality and independence between test modules

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed deps.py require_auth referencing removed REDACTED_FIELD field**
- **Found during:** Task 2 (full test suite run)
- **Issue:** src/backend/web/deps.py line 42 referenced `settings.REDACTED_FIELD` which no longer exists after field removal
- **Fix:** Updated require_auth to use `argon2.PasswordHasher().verify(settings.REDACTED_FIELD_hash, credentials.password)` with proper VerifyMismatchError handling
- **Files modified:** src/backend/web/deps.py
- **Verification:** All 271 tests pass including auth-dependent dashboard tests
- **Committed in:** db1a252 (Task 2 commit)

**2. [Rule 1 - Bug] Fixed test_podcast_service.py and test_repositories.py missing REDACTED_FIELD_hash**
- **Found during:** Task 2 (full test suite run)
- **Issue:** Two additional test files construct Settings() without the now-required REDACTED_FIELD_hash field
- **Fix:** Added argon2 import and TEST_HASH to both files, added REDACTED_FIELD_hash=TEST_HASH to all Settings() calls
- **Files modified:** tests/test_podcast_service.py, tests/test_repositories.py
- **Verification:** All 271 tests pass
- **Committed in:** db1a252 (Task 2 commit)

---

**Total deviations:** 2 auto-fixed (2 bugs from field removal)
**Impact on plan:** Both auto-fixes were necessary consequences of removing REDACTED_FIELD. No scope creep.

## Issues Encountered
None - all issues were direct consequences of the field removal and handled as deviations above.

## User Setup Required

After updating, users must:
1. Run `python -m src.hash_password` to generate an Argon2id hash
2. Add `DASHBOARD_PASSWORD_HASH=<hash>` to their `.env` file
3. The app will refuse to start until this is configured, showing a clear error checklist

## Next Phase Readiness
- Argon2id hash infrastructure is complete and verified
- Plan 05-02 can build on this to refine auth verification patterns
- Phase 6 (session auth) has the hash foundation it needs

## Self-Check: PASSED

- All 12 created/modified files verified present on disk
- All 3 task commits (59f71ef, c113a2a, db1a252) verified in git log
- Full test suite: 271/271 passed

---
*Phase: 05-secrets-and-configuration-foundation*
*Completed: 2026-03-09*
