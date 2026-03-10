# Requirements: Podcast Workflow

**Defined:** 2026-03-09
**Core Value:** Knowledge notes automatically become listenable podcast episodes with configurable voices and styles — no manual intervention required.

## v1.1 Requirements

Requirements for Security Hardening milestone. Each maps to roadmap phases.

### Secrets & History

- [ ] **SEC-01**: Git history is scrubbed of all committed secrets (.env, API keys) before open-source release
- [x] **SEC-02**: `.env.example` ships with placeholder values documenting all required env vars

### Authentication

- [x] **AUTH-01**: Dashboard password is stored as Argon2id hash, never plaintext
- [x] **AUTH-02**: CLI tool generates password hashes for `.env` configuration
- [x] **AUTH-03**: App refuses to start if password hash is missing or malformed
- [x] **AUTH-04**: Session-based auth replaces HTTP Basic Auth with signed cookies
- [x] **AUTH-05**: User can log in via a dedicated login page (not browser prompt)
- [x] **AUTH-06**: User can log out and session is invalidated
- [x] **AUTH-07**: Sessions expire after configurable timeout
- [x] **AUTH-08**: `/dashboard/status` endpoint requires authentication

### HTTP Hardening

- [x] **HTTP-01**: Login endpoint is rate-limited (max 5 attempts per 15 minutes per IP)
- [x] **HTTP-02**: Security headers are set on all responses (X-Content-Type-Options, X-Frame-Options, Referrer-Policy, HSTS)
- [x] **HTTP-03**: CORS policy restricts origins to configured allowlist
- [x] **HTTP-04**: CSRF protection covers all state-changing requests (POST, PUT, DELETE) via header-based tokens compatible with HTMX

### Path Validation

- [x] **PATH-01**: Preset folder paths are validated against a configurable base directory, rejecting traversal attempts
- [x] **PATH-02**: All file read/write operations validate paths are within allowed directories

## Future Requirements

Deferred to future milestones. Tracked but not in current roadmap.

### OpenClaw Integration

- **CLAW-01**: Success/fail status notifications sent to Telegram via OpenClaw
- **CLAW-02**: Review mode — audio sent to Telegram for approval before publishing
- **CLAW-03**: OpenClaw integration contract definition

### Audio Enhancement

- **AUD-01**: Intro/outro audio templates per podcast style
- **AUD-02**: Audio quality validation (SNR check)
- **AUD-03**: Fallback TTS provider for Gemini instability

### Distribution

- **DIST-01**: Cloud audio hosting (Cloudflare R2 or S3) for production RSS

## Out of Scope

Explicitly excluded. Documented to prevent scope creep.

| Feature | Reason |
|---------|--------|
| JWT tokens | Over-engineering for single-user app; signed session cookies are sufficient |
| OAuth2 / OIDC | No external identity provider needed for personal tool |
| Redis session store | In-memory sessions sufficient for single-user; no horizontal scaling needed |
| WAF / fail2ban integration | Infrastructure-level concern, not application responsibility |
| Role-based access control | Single user, no roles needed |
| Database-backed user management | Single user configured via env vars is sufficient |
| HTTPS termination in app | Handled by reverse proxy (nginx/Caddy) on VPS |
| Automated key rotation | Manual rotation sufficient for personal tool |
| CAPTCHA | Over-engineering; rate limiting is sufficient for single-user |
| Self-hosting HTMX/Pico CSS | Low priority; CDN is acceptable for now |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| SEC-01 | Phase 5 | Pending |
| SEC-02 | Phase 5 | Complete (05-01) |
| AUTH-01 | Phase 5 | Complete (05-02) |
| AUTH-02 | Phase 5 | Complete (05-01) |
| AUTH-03 | Phase 5 | Complete (05-01) |
| AUTH-04 | Phase 6 | Complete (06-01) |
| AUTH-05 | Phase 6 | Complete (06-02) |
| AUTH-06 | Phase 6 | Complete (06-02) |
| AUTH-07 | Phase 6 | Complete (06-01) |
| AUTH-08 | Phase 6 | Complete (06-01) |
| HTTP-01 | Phase 7 | Complete |
| HTTP-02 | Phase 7 | Complete |
| HTTP-03 | Phase 7 | Complete |
| HTTP-04 | Phase 7 | Complete |
| PATH-01 | Phase 8 | Complete (08-02) |
| PATH-02 | Phase 8 | Complete (08-02) |

**Coverage:**
- v1.1 requirements: 16 total
- Mapped to phases: 16
- Unmapped: 0

---
*Requirements defined: 2026-03-09*
*Last updated: 2026-03-10 — PATH-01, PATH-02 completed in Plan 08-02*
