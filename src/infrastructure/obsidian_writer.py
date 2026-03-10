"""Obsidian vault writer -- copies MP3 and creates episode markdown notes."""

import os
import shutil

from src.domain.models import Episode, sanitize_filename
from src.domain.path_validator import validate_path_within


def write_episode_to_vault(
    episode: Episode,
    mp3_source_path: str,
    transcript: str,
    vault_output_dir: str,
    vault_base_dir: str | None = None,
) -> tuple[str, str]:
    """Copy MP3 and create a markdown episode note in the Obsidian vault.

    The note includes YAML frontmatter with episode metadata, an Obsidian
    wiki-link audio embed, and a foldable transcript callout.

    Args:
        episode: Episode domain model with metadata.
        mp3_source_path: Path to the source MP3 file to copy.
        transcript: Full transcript text (newline-separated lines).
        vault_output_dir: Target directory inside the Obsidian vault.

    Returns:
        Tuple of (mp3_dest_path, note_dest_path).
    """
    if vault_base_dir is not None:
        validate_path_within(vault_output_dir, vault_base_dir)

    # Build date-prefixed base name with sanitized title
    date_str = episode.published_at.strftime("%Y-%m-%d")
    safe_title = sanitize_filename(episode.title)
    date_title = f"{date_str} - {safe_title}"

    mp3_filename = f"{date_title}.mp3"
    note_filename = f"{date_title}.md"

    # Ensure output directory exists
    os.makedirs(vault_output_dir, exist_ok=True)

    # Copy MP3 to vault
    mp3_dest = os.path.join(vault_output_dir, mp3_filename)
    shutil.copy2(mp3_source_path, mp3_dest)

    # Build markdown note content
    note_content = _build_note(episode, mp3_filename, transcript, date_str)

    # Write note to vault
    note_dest = os.path.join(vault_output_dir, note_filename)
    with open(note_dest, "w", encoding="utf-8") as f:
        f.write(note_content)

    return mp3_dest, note_dest


def _build_note(
    episode: Episode,
    mp3_filename: str,
    transcript: str,
    date_str: str,
) -> str:
    """Build the full markdown note content with frontmatter and transcript.

    Args:
        episode: Episode domain model with metadata.
        mp3_filename: Name of the MP3 file for the wiki link.
        transcript: Full transcript text.
        date_str: Formatted date string (YYYY-MM-DD).

    Returns:
        Complete markdown note as a string.
    """
    # Format hosts as YAML list
    hosts_yaml = "\n".join(f"  - {h}" for h in episode.hosts)

    frontmatter = (
        f"---\n"
        f"title: \"{episode.title}\"\n"
        f"date: \"{date_str}\"\n"
        f"episode_number: {episode.episode_number}\n"
        f"hosts:\n{hosts_yaml}\n"
        f"style: \"{episode.style_name}\"\n"
        f"source_file: \"{episode.source_file}\"\n"
        f"duration: \"{episode.duration_str}\"\n"
        f"tags:\n  - podcast\n  - episode\n"
        f"---\n"
    )

    # Build transcript callout with each line prefixed
    transcript_lines = transcript.split("\n")
    callout_lines = ["> [!note]- Transcript"]
    for line in transcript_lines:
        callout_lines.append(f"> {line}")
    callout_block = "\n".join(callout_lines)

    note = (
        f"{frontmatter}\n"
        f"# {episode.title}\n\n"
        f"![[{mp3_filename}]]\n\n"
        f"{callout_block}\n"
    )

    return note
