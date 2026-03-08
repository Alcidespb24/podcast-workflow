# Roadmap: Podcast Workflow

## Overview

Transform the existing prototype (Markdown to podcast audio) into a fully automated, end-to-end pipeline. The build sequence moves from configurable foundation and refactored pipeline core, through audio post-production and RSS distribution, into file-watching automation, and finally a web dashboard for managing it all. Each phase delivers a coherent, testable capability that builds on the last.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [x] **Phase 1: Foundation and Pipeline Refactor** - Data layer, configurable hosts/styles, single-call script generation, enhanced sanitizer
- [x] **Phase 2: Audio Processing and Distribution** - MP3 conversion, audio quality, RSS feed, Obsidian output (completed 2026-03-08)
- [x] **Phase 3: Automation** - File watcher, job queue, retry logic, rate-aware scheduling (completed 2026-03-08)
- [ ] **Phase 4: Web Dashboard** - Host/style/preset CRUD UI, job history, episode archive

## Phase Details

### Phase 1: Foundation and Pipeline Refactor
**Goal**: Users can configure podcast hosts and styles, and the pipeline produces quality multi-speaker scripts from any Obsidian markdown note using those configurations
**Depends on**: Nothing (first phase)
**Requirements**: PIPE-01, PIPE-02, PIPE-03, PIPE-04, PIPE-05, PIPE-06, PIPE-07, PREP-01, PREP-02, DATA-01, DATA-02, DATA-03
**Success Criteria** (what must be TRUE):
  1. User can create and persist host configurations (name, voice, personality, role) and style configurations (tone, length, structure, speaker count) in the database
  2. User can run the pipeline against any Obsidian markdown file and receive a coherent multi-speaker podcast script that uses configured host/style presets
  3. Obsidian-specific syntax (callouts, embeds, Mermaid, Dataview, math, comments, highlights, tags, block IDs, footnotes) is stripped cleanly before script generation
  4. The pipeline enforces a 2-speaker maximum and validates speaker names between LLM output and TTS config before synthesis
  5. Schema migrations work via Alembic and configuration loads via pydantic-settings
**Plans:** 5 plans

Plans:
- [x] 01-01-PLAN.md -- Test infrastructure, domain models (Host/Style/PipelineConfig), pydantic-settings configuration
- [x] 01-02-PLAN.md -- Expanded Obsidian sanitizer (12+ syntax patterns)
- [x] 01-03-PLAN.md -- ORM models, repositories, Alembic migrations, default data seeding
- [x] 01-04-PLAN.md -- Pipeline refactor: config-driven prompt builder, script chunker, speaker validation, service wiring
- [x] 01-05-PLAN.md -- Gap closure: fix Alembic migration idempotency (replace Base.metadata.create_all with programmatic Alembic upgrade)

### Phase 2: Audio Processing and Distribution
**Goal**: Pipeline output is broadcast-ready MP3 with proper metadata, published to a valid RSS feed, with episode notes saved back to Obsidian
**Depends on**: Phase 1
**Requirements**: AUDIO-01, AUDIO-02, AUDIO-03, AUDIO-04, DIST-01, DIST-02, DIST-03, DIST-04, OBS-01, OBS-02
**Success Criteria** (what must be TRUE):
  1. Generated audio has smooth transitions between chunks (no clicks, pops, or silence gaps at boundaries)
  2. Pipeline outputs a properly tagged MP3 file (ID3: title, artist, episode number) at CBR 128kbps mono
  3. An RSS feed with iTunes namespace tags is generated, validates successfully, and is served via HTTP for Spotify ingestion
  4. MP3 file and a markdown note (with metadata, transcript, and audio link) are saved to the configured Obsidian vault folder
**Plans:** 4/4 plans complete

Plans:
- [x] 02-01-PLAN.md -- Episode model, DB persistence, config extension, dependency installation
- [x] 02-02-PLAN.md -- Audio processing pipeline: crossfade, RMS normalization, MP3 export, ID3 tagging
- [ ] 02-03-PLAN.md -- RSS feed generation + validation, FastAPI app skeleton, Obsidian vault writer
- [ ] 02-04-PLAN.md -- Pipeline integration: wire audio/RSS/Obsidian into podcast_service, end-to-end verification

### Phase 3: Automation
**Goal**: Users can drop a markdown file into a watched Obsidian folder and a podcast episode is produced end-to-end without manual intervention
**Depends on**: Phase 2
**Requirements**: AUTO-01, AUTO-02, AUTO-03, AUTO-04, AUTO-05, AUTO-06
**Success Criteria** (what must be TRUE):
  1. Dropping a .md file into a watched vault folder triggers the full pipeline automatically (with 1-2s debounce, no duplicate processing)
  2. Each watched folder maps to a specific host/style preset, and different folders produce episodes with different configurations
  3. Jobs are tracked in SQLite with state progression (pending through complete/failed) and appear in job history
  4. Failed TTS/LLM calls retry with exponential backoff, and API rate limits are respected without crashing
**Plans:** 3/3 plans complete

Plans:
- [ ] 03-01-PLAN.md -- Domain models (Preset/Job/JobState), ORM records, repositories, Alembic migration, Settings extension
- [ ] 03-02-PLAN.md -- Debounced watchdog handler for .md files, 429-aware retry with exponential backoff
- [ ] 03-03-PLAN.md -- Job processor, watcher service, FastAPI lifespan integration, standalone CLI

### Phase 4: Web Dashboard
**Goal**: Users can manage all podcast configuration and view episode history through a browser-based interface
**Depends on**: Phase 3
**Requirements**: DASH-01, DASH-02, DASH-03, DASH-04, DASH-05, DASH-06
**Success Criteria** (what must be TRUE):
  1. User can create, edit, and delete hosts and styles through the web UI
  2. User can assign host/style presets to vault folders through the web UI
  3. User can browse past episodes with status, metadata, and an in-browser audio player
  4. Dashboard is served via FastAPI with HTMX (no JS build step), protected by authentication, and bound to localhost by default
**Plans**: TBD

Plans:
- [ ] 04-01: TBD
- [ ] 04-02: TBD

## Progress

**Execution Order:**
Phases execute in numeric order: 1 -> 2 -> 3 -> 4

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Foundation and Pipeline Refactor | 5/5 | Complete | 2026-03-07 |
| 2. Audio Processing and Distribution | 4/4 | Complete    | 2026-03-08 |
| 3. Automation | 3/3 | Complete   | 2026-03-08 |
| 4. Web Dashboard | 0/2 | Not started | - |
