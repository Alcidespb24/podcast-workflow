# Requirements: Podcast Workflow

**Defined:** 2026-03-07
**Core Value:** Knowledge notes automatically become listenable podcast episodes with configurable voices and styles

## v1 Requirements

### Pipeline Core

- [x] **PIPE-01**: Hosts are configurable with name, TTS voice, personality traits, and role
- [x] **PIPE-02**: Podcast styles are configurable with tone, target length, structure, and speaker count
- [x] **PIPE-03**: Full podcast script generated in one LLM call (not per-chunk) to preserve conversation continuity
- [x] **PIPE-04**: Generated script chunked at TTS stage (not content stage) with speaker-turn-aware boundaries
- [x] **PIPE-05**: Speaker names validated/normalized between LLM output and TTS config before synthesis
- [x] **PIPE-06**: 2-speaker maximum enforced in domain model and all configuration surfaces
- [x] **PIPE-07**: Clean architecture maintained across all new components (domain/infrastructure/application/backend)

### Content Preprocessing

- [x] **PREP-01**: Obsidian sanitizer expanded to handle callouts, embeds, Mermaid, Dataview, math blocks, comments, highlights, tags, block IDs, footnotes, and strikethrough
- [x] **PREP-02**: Fallback splitting for single paragraphs exceeding chunk size (sentence-level split)

### Audio Processing

- [x] **AUDIO-01**: Audio crossfading at chunk boundaries (20-50ms overlap) to eliminate artifacts
- [x] **AUDIO-02**: Volume normalization across segments (RMS normalization)
- [x] **AUDIO-03**: WAV to MP3 conversion (CBR 128kbps mono) via pydub + ffmpeg
- [x] **AUDIO-04**: ID3 tags on MP3 files (title, artist, episode number)

### Automation

- [ ] **AUTO-01**: File watcher (watchdog) monitors configured vault sub-folders for new .md files
- [ ] **AUTO-02**: Debouncing (1-2s) and deduplication to handle Windows duplicate events
- [ ] **AUTO-03**: Folder-to-preset mapping: each watched folder maps to a host/style configuration
- [ ] **AUTO-04**: SQLite job queue with state tracking (pending, processing, encoding, publishing, complete, failed)
- [ ] **AUTO-05**: Retry with exponential backoff on TTS/LLM failures
- [ ] **AUTO-06**: Rate-aware scheduling respecting Gemini API limits

### Distribution

- [x] **DIST-01**: RSS feed generation with iTunes namespace tags via feedgen
- [x] **DIST-02**: MP3 hosting via FastAPI static file serving
- [x] **DIST-03**: Episode metadata (title, description, tags) in RSS feed
- [x] **DIST-04**: RSS feed validation before publishing

### Obsidian Integration

- [x] **OBS-01**: MP3 audio file saved to configured Obsidian vault folder
- [x] **OBS-02**: Markdown note created with episode metadata, transcript, and link to audio

### Web Dashboard

- [ ] **DASH-01**: Host CRUD — create, edit, delete podcast hosts via web UI
- [ ] **DASH-02**: Style CRUD — create, edit, delete podcast styles via web UI
- [ ] **DASH-03**: Folder preset mapping — assign host/style configs to vault folders
- [ ] **DASH-04**: Job/episode history — view past episodes with status, audio player, metadata
- [ ] **DASH-05**: FastAPI + HTMX + Jinja2 stack (no JS build step)
- [ ] **DASH-06**: Authentication (at minimum HTTP Basic Auth, bind to 127.0.0.1 by default)

### Data Layer

- [x] **DATA-01**: SQLite database with SQLAlchemy ORM for hosts, styles, presets, episodes
- [x] **DATA-02**: Alembic migrations for schema evolution
- [x] **DATA-03**: Pydantic-settings for configuration management

## v2 Requirements

### Notifications

- **NOTF-01**: OpenClaw status notification (success/fail → Telegram)
- **NOTF-02**: Review mode — audio sent to Telegram for approve/reject before publishing
- **NOTF-03**: OpenClaw integration contract definition

### Enhancements

- **ENH-01**: Intro/outro audio templates per podcast style
- **ENH-02**: Audio quality validation (SNR check, reject degraded TTS output)
- **ENH-03**: Fallback TTS provider for Gemini instability periods
- **ENH-04**: Cloud audio hosting (Cloudflare R2 or S3) for production RSS

## Out of Scope

| Feature | Reason |
|---------|--------|
| Video podcasts | Audio only — massive complexity for minimal value |
| Voice cloning | Legal/ethical concerns, Gemini TTS doesn't support it |
| Real-time streaming | Batch pipeline, completely different architecture |
| Mobile app | Web dashboard accessible from phone browser |
| Obsidian TypeScript plugin | Stay in Python, interact via filesystem |
| AI-generated cover art | Out of scope — manual or template-based |
| Multi-language translation | Single language per episode |
| Complex scheduling (cron) | OpenClaw handles scheduling externally |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| PIPE-01 | Phase 1 | Complete |
| PIPE-02 | Phase 1 | Complete |
| PIPE-03 | Phase 1 | Complete |
| PIPE-04 | Phase 1 | Complete |
| PIPE-05 | Phase 1 | Complete |
| PIPE-06 | Phase 1 | Complete |
| PIPE-07 | Phase 1 | Complete |
| PREP-01 | Phase 1 | Complete |
| PREP-02 | Phase 1 | Complete |
| DATA-01 | Phase 1 | Complete |
| DATA-02 | Phase 1 | Complete |
| DATA-03 | Phase 1 | Complete |
| AUDIO-01 | Phase 2 | Complete |
| AUDIO-02 | Phase 2 | Complete |
| AUDIO-03 | Phase 2 | Complete |
| AUDIO-04 | Phase 2 | Complete |
| DIST-01 | Phase 2 | Complete |
| DIST-02 | Phase 2 | Complete |
| DIST-03 | Phase 2 | Complete |
| DIST-04 | Phase 2 | Complete |
| OBS-01 | Phase 2 | Complete |
| OBS-02 | Phase 2 | Complete |
| AUTO-01 | Phase 3 | Pending |
| AUTO-02 | Phase 3 | Pending |
| AUTO-03 | Phase 3 | Pending |
| AUTO-04 | Phase 3 | Pending |
| AUTO-05 | Phase 3 | Pending |
| AUTO-06 | Phase 3 | Pending |
| DASH-01 | Phase 4 | Pending |
| DASH-02 | Phase 4 | Pending |
| DASH-03 | Phase 4 | Pending |
| DASH-04 | Phase 4 | Pending |
| DASH-05 | Phase 4 | Pending |
| DASH-06 | Phase 4 | Pending |

**Coverage:**
- v1 requirements: 34 total
- Mapped to phases: 34
- Unmapped: 0

---
*Requirements defined: 2026-03-07*
*Traceability updated: 2026-03-08 (02-02)*
