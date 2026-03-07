# Podcast Workflow

## What This Is

An automated pipeline tool that watches an Obsidian vault for new markdown files, generates multi-speaker podcast scripts using an LLM, converts them to audio via Google Gemini TTS, publishes episodes to an RSS feed (for Spotify distribution), and saves output back to Obsidian. A web dashboard provides control over hosts, podcast styles, and folder-to-preset mappings. OpenClaw handles orchestration notifications via Telegram.

## Core Value

Knowledge notes automatically become listenable podcast episodes with configurable voices and styles — no manual intervention required.

## Requirements

### Validated

(None yet — ship to validate)

### Active

- [ ] File watcher monitors dedicated sub-folders in the local Obsidian vault for new MD files
- [ ] Markdown preprocessor sanitizes content (strips code blocks, tables, front-matter, ASCII diagrams, wiki links)
- [ ] Script generator uses LLM (Gemini 2.5 Pro) to create multi-speaker podcast scripts from sanitized content
- [ ] Configurable hosts with name, TTS voice, personality traits, and role (host/co-host/guest/interviewer)
- [ ] Configurable podcast styles with tone, target length, structure (free-flowing vs segments), and speaker count
- [ ] Folder-based preset mapping: different vault sub-folders map to different host/style configurations
- [ ] Google Gemini TTS generates multi-speaker audio from the script, chunking long content automatically
- [ ] Audio file (.wav/.mp3) saved back into the Obsidian vault
- [ ] Markdown note with metadata, transcript, and episode link saved to Obsidian
- [ ] Audio published to an RSS feed that Spotify can pull from
- [ ] OpenClaw notified of pipeline status (success/fail) for Telegram relay
- [ ] Two execution modes: fully automated (publish immediately) and review mode (OpenClaw sends audio to Telegram for approval before publishing)
- [ ] Web dashboard for managing hosts, styles, and folder-to-preset mappings

### Out of Scope

- OpenClaw development — external system, this tool only sends status notifications to it
- Spotify account/platform setup — handled manually; this tool produces the RSS feed
- Mobile app — web dashboard is sufficient
- Video podcast — audio only

## Context

- A working prototype exists: MD → sanitize → LLM script generation → Gemini TTS → WAV output
- The codebase follows clean architecture: domain, infrastructure, application, backend layers
- OpenClaw is an agent running on a VPS that communicates via Telegram and reads/writes to the Obsidian vault
- The Obsidian vault is on the local filesystem (same machine as this tool)
- Gemini TTS has input size limits; content is already chunked at paragraph boundaries (~12k chars per chunk)
- Custom exceptions are in place: ConfigurationError, InputError, TTSError, AudioWriteError
- Available Gemini TTS voices include Kore, Puck, and others for multi-speaker configs

## Constraints

- **TTS Provider**: Google Gemini TTS — multi-speaker support required, limits chunk sizes
- **LLM Provider**: Google Gemini 2.5 Pro — used for script generation
- **Vault Access**: Local filesystem only — no cloud sync or API needed
- **Notification**: Must integrate with OpenClaw's expected interface (TBD exact protocol)
- **RSS Hosting**: Platform not yet decided — needs research

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Two-step pipeline (LLM script → TTS audio) | TTS model can only speak pre-written scripts, not generate content | ✓ Good |
| Folder-based preset mapping | Simple, leverages existing Obsidian organization, no complex rule engine | — Pending |
| Web dashboard for config | Accessible from any device, better UX than CLI for managing hosts/styles | — Pending |
| Configurable hosts (name, voice, personality, role) | Different topics benefit from different presentation styles | — Pending |

---
*Last updated: 2026-03-07 after initialization*
