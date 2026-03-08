"""Podcast generation pipeline — orchestrates all stages from MD to Episode."""

import logging
import os
import re
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy.orm import Session

from src.backend.google.script_generator import GoogleScriptGenerator
from src.backend.google.tts import GoogleTTSClient
from src.config import Settings
from src.domain.models import Episode, PipelineConfig, sanitize_filename
from src.domain.prompt_builder import build_script_prompt
from src.exceptions import RSSError
from src.infrastructure.audio import export_tagged_mp3, process_audio
from src.infrastructure.chunker import chunk_script, normalize_speakers, validate_speakers
from src.infrastructure.database.repositories import EpisodeRepository
from src.infrastructure.obsidian_writer import write_episode_to_vault
from src.infrastructure.reader import read_md_files
from src.infrastructure.rss import build_podcast_feed, validate_podcast_rss
from src.infrastructure.sanitizer import sanitize_markdown

logger = logging.getLogger(__name__)

_H1_RE = re.compile(r"^#\s+(.+)$", re.MULTILINE)


def _extract_title(content: str, source_file: str) -> str:
    """Extract episode title from first H1 heading, falling back to filename stem."""
    match = _H1_RE.search(content)
    if match:
        return match.group(1).strip()
    return Path(source_file).stem


def _extract_description(clean_content: str, max_length: int = 200) -> str:
    """Extract episode description from sanitized content, truncated at word boundary."""
    text = clean_content.strip()
    if len(text) <= max_length:
        return text
    # Truncate at last space before max_length to avoid cutting mid-word
    truncated = text[:max_length]
    last_space = truncated.rfind(" ")
    if last_space > 0:
        truncated = truncated[:last_space]
    return truncated


def generate_podcast(
    config: PipelineConfig,
    settings: Settings,
    session: Session,
) -> Episode:
    """Run the full podcast generation pipeline.

    Flow:
        1. Read source markdown
        2. Sanitize for TTS consumption
        3. Build config-driven prompt
        4. Generate script (single LLM call)
        5. Normalize and validate speaker labels
        6. Chunk script at speaker-turn boundaries
        7. Synthesize audio per chunk
        8. Extract episode metadata
        9. Process audio (crossfade + RMS normalization)
        10. Export tagged MP3
        11. Persist Episode to database
        12. Regenerate RSS feed
        13. Write to Obsidian vault
        14. Return Episode

    Args:
        config: Pipeline configuration with hosts, style, and source file.
        settings: Application settings (API keys, directories, etc.).
        session: SQLAlchemy session for Episode persistence.

    Returns:
        The persisted Episode domain model.
    """
    host_names = [h.name for h in config.hosts]

    # 1. Read source content
    content = read_md_files([config.source_file])

    # 2. Sanitize markdown
    clean_content = sanitize_markdown(content)

    # 3. Build prompt
    prompt = build_script_prompt(clean_content, config.hosts, config.style)

    # 4. Generate script — single call
    script_gen = GoogleScriptGenerator(api_key=settings.google_api_key)
    script = script_gen.generate(prompt)

    # 5. Normalize speaker labels, then validate
    script = normalize_speakers(script, host_names)
    valid, unexpected = validate_speakers(script, host_names)
    if not valid:
        logger.warning(
            "Unexpected speaker names in generated script: %s. "
            "Continuing with best-effort output.",
            unexpected,
        )

    # 6. Chunk at speaker-turn boundaries
    chunks = chunk_script(script, host_names)
    logger.info("Script split into %d chunk(s) for TTS.", len(chunks))

    # 7. Synthesize audio per chunk
    tts = GoogleTTSClient(api_key=settings.google_api_key)
    audio_segments: list[bytes] = []
    for i, chunk in enumerate(chunks, 1):
        logger.info("Synthesizing chunk %d/%d...", i, len(chunks))
        audio_segments.append(tts.synthesize(chunk, config.hosts))

    # 8. Extract episode metadata
    title = _extract_title(content, config.source_file)
    description = _extract_description(clean_content)
    episode_number = EpisodeRepository(session).get_next_episode_number()

    # 9. Process audio (crossfade + RMS normalization)
    combined = process_audio(
        audio_segments,
        crossfade_ms=settings.crossfade_ms,
        target_dbfs=settings.target_dbfs,
    )
    duration_seconds = combined.duration_seconds

    # 10. Export tagged MP3
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    safe_title = sanitize_filename(title)
    filename = f"{today} - {safe_title}.mp3"
    os.makedirs(settings.episodes_dir, exist_ok=True)
    export_path = os.path.join(settings.episodes_dir, filename)

    export_tagged_mp3(
        combined,
        export_path,
        title=title,
        artist=settings.podcast_name,
        track_number=episode_number,
    )
    file_size = os.path.getsize(export_path)

    # 11. Persist Episode to database
    episode = Episode(
        title=title,
        description=description,
        episode_number=episode_number,
        filename=filename,
        duration_seconds=duration_seconds,
        file_size=file_size,
        hosts=host_names,
        style_name=config.style.name,
        source_file=config.source_file,
        published_at=datetime.now(timezone.utc),
    )
    repo = EpisodeRepository(session)
    episode = repo.create(episode)
    session.commit()

    # 12. Regenerate RSS feed
    try:
        all_episodes = repo.get_all()
        feed_xml = build_podcast_feed(
            settings.podcast_name,
            f"{settings.podcast_name} - auto-generated podcast feed",
            settings.base_url,
            all_episodes,
        )
        validation_errors = validate_podcast_rss(feed_xml)
        if validation_errors:
            logger.warning("RSS validation warnings: %s", validation_errors)

        feed_path = os.path.join(settings.episodes_dir, "feed.xml")
        with open(feed_path, "w", encoding="utf-8") as f:
            f.write(feed_xml)
        logger.info("RSS feed written to %s", feed_path)
    except RSSError as exc:
        logger.error("RSS feed generation failed (non-fatal): %s", exc)

    # 13. Write to Obsidian vault
    mp3_dest, note_dest = write_episode_to_vault(
        episode, export_path, script, settings.vault_output_dir
    )
    logger.info("Vault output: MP3=%s, Note=%s", mp3_dest, note_dest)

    # 14. Return Episode
    return episode
