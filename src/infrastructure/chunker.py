"""Speaker-turn-aware script chunker and speaker validation utilities."""

import re

_SPEAKER_LABEL_RE = re.compile(r"^(\w+):", re.MULTILINE)
_SENTENCE_BOUNDARY_RE = re.compile(r"(?<=[.!?])\s+")


def chunk_script(
    script: str, host_names: list[str], max_chars: int = 12000
) -> list[str]:
    """Split a podcast script into chunks at speaker-turn boundaries.

    Parses the script into individual speaker turns (lines starting with
    ``Name: ``), then groups consecutive turns into chunks that stay under
    *max_chars*. When a single turn exceeds the limit, it falls back to
    sentence-level splitting.

    Args:
        script: Full podcast script text.
        host_names: Expected speaker names (used to detect turn boundaries).
        max_chars: Soft maximum character count per chunk.

    Returns:
        Ordered list of script chunks.
    """
    turns = _parse_turns(script, host_names)

    if not turns:
        return [script] if script.strip() else []

    chunks: list[str] = []
    current_parts: list[str] = []
    current_len = 0

    for turn in turns:
        turn_len = len(turn)
        separator_len = 1 if current_parts else 0  # newline between turns

        if current_parts and current_len + separator_len + turn_len > max_chars:
            chunks.append("\n".join(current_parts))
            current_parts = []
            current_len = 0

        if turn_len > max_chars and not current_parts:
            # Single oversized turn: split at sentence boundaries
            chunks.extend(_split_sentences(turn, max_chars))
        else:
            current_parts.append(turn)
            current_len += turn_len + separator_len

    if current_parts:
        chunks.append("\n".join(current_parts))

    return chunks


def validate_speakers(
    script: str, expected_names: list[str]
) -> tuple[bool, set[str]]:
    """Check that all speaker labels in the script match expected names.

    Detection is case-sensitive: ``joe:`` is flagged if ``Joe`` is expected.

    Args:
        script: Podcast script text.
        expected_names: List of valid speaker names.

    Returns:
        Tuple of (is_valid, set_of_unexpected_names).
    """
    found = set(_SPEAKER_LABEL_RE.findall(script))
    expected_set = set(expected_names)
    unexpected = found - expected_set
    return (len(unexpected) == 0, unexpected)


def normalize_speakers(script: str, expected_names: list[str]) -> str:
    """Fix case mismatches in speaker labels.

    Performs case-insensitive replacement of speaker-name prefixes at line
    starts, correcting e.g. ``joe:`` to ``Joe:``.

    Args:
        script: Podcast script text.
        expected_names: Canonical speaker names with correct casing.

    Returns:
        Script with normalized speaker labels.
    """
    result = script
    for name in expected_names:
        pattern = re.compile(rf"^({re.escape(name)}):", re.MULTILINE | re.IGNORECASE)
        result = pattern.sub(f"{name}:", result)
    return result


def _parse_turns(script: str, host_names: list[str]) -> list[str]:
    """Parse script into individual speaker turns.

    A turn starts when a line begins with one of the host names followed
    by a colon. All subsequent lines until the next turn belong to the
    same turn.
    """
    if not host_names:
        return [script]

    escaped = "|".join(re.escape(n) for n in host_names)
    pattern = re.compile(rf"^(?={escaped}:)", re.MULTILINE)

    parts = pattern.split(script)
    return [p.strip() for p in parts if p.strip()]


def _split_sentences(text: str, max_chars: int) -> list[str]:
    """Split text at sentence boundaries when a single turn is too long."""
    sentences = _SENTENCE_BOUNDARY_RE.split(text)

    chunks: list[str] = []
    current: list[str] = []
    current_len = 0

    for sentence in sentences:
        sep_len = 1 if current else 0
        if current and current_len + sep_len + len(sentence) > max_chars:
            chunks.append(" ".join(current))
            current = [sentence]
            current_len = len(sentence)
        else:
            current.append(sentence)
            current_len += sep_len + len(sentence)

    if current:
        chunks.append(" ".join(current))

    return chunks
