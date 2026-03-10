# Roadmap: Podcast Workflow

## Milestones

- ✅ **v1.0 MVP** — Phases 1-4 (shipped 2026-03-09)
- ✅ **v1.1 Security Hardening** — Phases 5-8 (shipped 2026-03-10)

## Phases

<details>
<summary>✅ v1.0 MVP (Phases 1-4) — SHIPPED 2026-03-09</summary>

- [x] Phase 1: Foundation and Pipeline Refactor (5/5 plans) — completed 2026-03-07
- [x] Phase 2: Audio Processing and Distribution (4/4 plans) — completed 2026-03-08
- [x] Phase 3: Automation (3/3 plans) — completed 2026-03-08
- [x] Phase 4: Web Dashboard (4/4 plans) — completed 2026-03-09

See: `.planning/milestones/v1.0-ROADMAP.md` for full details.

</details>

### ✅ v1.1 Security Hardening (Complete)

**Milestone Goal:** Harden the application for VPS deployment and open-source readiness — eliminate all security vulnerabilities found in audit.

- [x] **Phase 5: Secrets and Configuration Foundation** - Scrub git history, migrate to env-based secrets, implement password hashing infrastructure
- [x] **Phase 6: Authentication Overhaul** - Replace HTTP Basic Auth with session-based auth, login/logout pages, session management (completed 2026-03-10)
- [x] **Phase 7: HTTP Hardening** - Rate limiting, CSRF protection, security headers, CORS policy (completed 2026-03-10)
- [x] **Phase 8: Path Validation** - Prevent path traversal on all file operations and preset folder paths (completed 2026-03-10)

## Phase Details

### Phase 5: Secrets and Configuration Foundation
**Goal**: All secrets are removed from git history and loaded exclusively from environment variables, with password hashing infrastructure ready for auth overhaul
**Depends on**: Phase 4 (v1.0 complete)
**Requirements**: SEC-01, SEC-02, AUTH-01, AUTH-02, AUTH-03
**Success Criteria** (what must be TRUE):
  1. Running `git log -p` across full history shows zero API keys, passwords, or `.env` values
  2. `.env.example` exists with placeholder values documenting every required environment variable
  3. Dashboard password in `.env` is an Argon2id hash, and the app verifies login against it
  4. Running `python -m podcast_workflow.hash_password` (or equivalent CLI) outputs a valid Argon2id hash for a given password
  5. App refuses to start with a clear error message if `DASHBOARD_PASSWORD_HASH` is missing or not a valid Argon2id hash
**Plans:** 2 plans

Plans:
- [x] 05-01-PLAN.md — Config foundation: Argon2id hash field, CLI tool, .env.example, startup validation
- [x] 05-02-PLAN.md — Auth integration: Wire Argon2id verification into require_auth

### Phase 6: Authentication Overhaul
**Goal**: Users authenticate via a dedicated login page with session-based auth, replacing the browser HTTP Basic Auth prompt entirely
**Depends on**: Phase 5 (password hashing infrastructure)
**Requirements**: AUTH-04, AUTH-05, AUTH-06, AUTH-07, AUTH-08
**Success Criteria** (what must be TRUE):
  1. Visiting any dashboard page while unauthenticated redirects to a styled login page (no browser prompt)
  2. After successful login, user receives a signed session cookie and can navigate all dashboard pages without re-authenticating
  3. Clicking logout invalidates the session and redirects to the login page; the old session cookie no longer grants access
  4. A session left idle beyond the configured timeout requires re-authentication on the next request
  5. Hitting `/dashboard/status` without a valid session returns 401 (or redirects to login), not the status data
**Plans:** 2/2 plans complete

Plans:
- [x] 06-01-PLAN.md — Session infrastructure: SessionMiddleware, require_auth rewrite, status endpoint auth, test overhaul
- [x] 06-02-PLAN.md — Login/logout UI: branded login page, auth endpoints, sidebar logout button

### Phase 7: HTTP Hardening
**Goal**: The application resists brute-force attacks, cross-site request forgery, and common HTTP-level exploits
**Depends on**: Phase 6 (sessions required for CSRF token binding; login endpoint must exist for rate limiting)
**Requirements**: HTTP-01, HTTP-02, HTTP-03, HTTP-04
**Success Criteria** (what must be TRUE):
  1. After 5 failed login attempts from the same IP within 15 minutes, the 6th attempt returns 429 Too Many Requests
  2. Every HTTP response includes X-Content-Type-Options, X-Frame-Options, Referrer-Policy, and Strict-Transport-Security headers
  3. A cross-origin request from an unlisted origin is rejected by CORS policy; a request from a configured origin succeeds
  4. All HTMX-driven POST, PUT, and DELETE operations (host/style/preset CRUD) continue working with CSRF tokens attached via `hx-headers`; a request missing the CSRF token is rejected with 403
**Plans:** 2/2 plans complete

Plans:
- [x] 07-01-PLAN.md — Rate limiting, security headers, and CORS policy
- [x] 07-02-PLAN.md — CSRF protection with HTMX-compatible header-based tokens

### Phase 8: Path Validation
**Goal**: All file system operations are confined to allowed directories, preventing path traversal attacks
**Depends on**: Phase 5 (configuration foundation); can run in parallel with Phase 7
**Requirements**: PATH-01, PATH-02
**Success Criteria** (what must be TRUE):
  1. Creating or updating a preset with a folder path containing `../` or absolute paths outside the configured base directory is rejected with a clear validation error
  2. Any file read/write operation (episode output, markdown input, audio export) that would resolve outside allowed directories is blocked before touching the filesystem
**Plans:** 2/2 plans complete

Plans:
- [x] 08-01-PLAN.md — Path validator foundation: PathTraversalError, validate_path_within, VAULT_BASE_DIR config, test infrastructure
- [x] 08-02-PLAN.md — Wire validation into preset routes, watcher, reader, writer, and UI (inline errors, warning badges)

## Progress

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 1. Foundation and Pipeline Refactor | v1.0 | 5/5 | Complete | 2026-03-07 |
| 2. Audio Processing and Distribution | v1.0 | 4/4 | Complete | 2026-03-08 |
| 3. Automation | v1.0 | 3/3 | Complete | 2026-03-08 |
| 4. Web Dashboard | v1.0 | 4/4 | Complete | 2026-03-09 |
| 5. Secrets and Configuration Foundation | v1.1 | 2/2 | Complete | 2026-03-09 |
| 6. Authentication Overhaul | v1.1 | Complete    | 2026-03-10 | 2026-03-10 |
| 7. HTTP Hardening | v1.1 | 2/2 | Complete | 2026-03-10 |
| 8. Path Validation | v1.1 | 2/2 | Complete | 2026-03-10 |
