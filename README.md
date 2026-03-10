# Podcast Workflow

Automated pipeline that watches an Obsidian vault for markdown files, generates multi-speaker podcast scripts via Gemini, converts them to broadcast-ready MP3 audio, publishes to an iTunes-compliant RSS feed, and provides a web dashboard for configuration.

## Architecture

Clean architecture with four layers:

| Layer | Path | Responsibility |
|---|---|---|
| Domain | `src/domain/` | Models, prompt builder, exceptions |
| Infrastructure | `src/infrastructure/` | Database, audio processing, sanitizer, RSS, Obsidian writer |
| Application | `src/application/` | Pipeline orchestration, job processor, retry logic |
| Backend | `src/backend/` | Gemini API clients, file watcher, FastAPI dashboard |

## Setup

### Prerequisites

- Python >= 3.12
- [uv](https://docs.astral.sh/uv/) (package manager)
- [ffmpeg](https://ffmpeg.org/) (audio encoding)
- A [Google Gemini API key](https://aistudio.google.com/apikey)

### Install

```bash
uv sync
```

### Configure

Create a `.env` file:

```env
GOOGLE_API_KEY = "your-gemini-api-key"
BASE_URL = "https://your-public-url"
VAULT_OUTPUT_DIR = "/path/to/obsidian/vault/podcasts"
```

See [Configuration](#configuration) for all available settings.

### Database

Migrations run automatically on startup via Alembic. Default hosts (Joe & Jane) and style are seeded on first run.

## Usage

### Web Dashboard (recommended)

```bash
python run_dashboard.py
```

Opens at `http://127.0.0.1:8000/dashboard/episodes`. Includes file watcher, job processor, and episode management UI.

### Standalone Watcher

```bash
python -m src watch
```

Monitors preset folders and processes jobs without the web UI.

### One-shot

```bash
python main.py path/to/file.md
```

Generates a single podcast episode from a markdown file.

## Pipeline

```
Markdown → Sanitize → Gemini 2.5 Pro (script) → Chunk → Gemini TTS (audio)
  → Crossfade + Normalize → MP3 + ID3 tags → RSS feed → Obsidian vault
```

## Automation

The watcher monitors preset folders for new markdown files and processes them automatically. Any tool or bot that drops `.md` files into a watched folder can trigger episode generation.

For example, [OpenClaw](https://github.com/openclaw/openclaw) (a Telegram-connected AI agent) can write research notes to your Obsidian vault throughout the day. Pair that with a scheduled task (cron, Windows Task Scheduler, etc.) that runs the pipeline each morning, and new episodes appear in your RSS feed on autopilot.

## Episode Frontmatter

Markdown files can include optional YAML frontmatter to override auto-extracted metadata:

```yaml
---
title: "Custom Episode Title"
description: "A concise summary for podcast apps like Spotify."
cover_url: "https://example.com/episode-art.jpg"
---
```

| Field | Fallback |
|---|---|
| `title` | First H1 heading, then filename |
| `description` | First 200 chars of sanitized content |
| `cover_url` | Channel-level cover art |

## Configuration

| Setting | Default | Description |
|---|---|---|
| `GOOGLE_API_KEY` | *(required)* | Gemini API key |
| `BASE_URL` | *(required)* | Public HTTPS URL for RSS enclosures |
| `VAULT_OUTPUT_DIR` | *(required)* | Obsidian vault output path |
| `DATABASE_URL` | `sqlite:///data/podcast.db` | SQLite database path |
| `PODCAST_NAME` | `My Knowledge Podcast` | RSS channel title |
| `PODCAST_DESCRIPTION` | | RSS channel description |
| `PODCAST_EMAIL` | | Owner email for RSS feed |
| `PODCAST_COVER_URL` | | Cover art URL for RSS feed |
| `EPISODES_DIR` | `episodes` | Local MP3 storage directory |
| `CROSSFADE_MS` | `30` | Audio crossfade in milliseconds |
| `TARGET_DBFS` | `-20.0` | RMS normalization target |
| `DASHBOARD_USERNAME` | `admin` | Dashboard login username |
| `DASHBOARD_PASSWORD_HASH` | *(required)* | Argon2id hash — generate with `python -m src.hash_password` |
| `WATCHER_ENABLED` | `true` | Enable file watching |
| `MAX_RETRIES` | `3` | Job retry limit |

## Testing

```bash
pytest
```

## License

[MIT](LICENSE)
