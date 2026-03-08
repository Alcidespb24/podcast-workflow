"""Podcast generation pipeline — orchestrates all stages from MD to WAV."""

import logging

from src.backend.google.script_generator import GoogleScriptGenerator
from src.backend.google.tts import GoogleTTSClient
from src.config import Settings
from src.domain.models import PipelineConfig
from src.domain.prompt_builder import build_script_prompt
from src.infrastructure.audio import write_wav
from src.infrastructure.chunker import chunk_script, normalize_speakers, validate_speakers
from src.infrastructure.reader import read_md_files
from src.infrastructure.sanitizer import sanitize_markdown

logger = logging.getLogger(__name__)


def generate_podcast(
    config: PipelineConfig,
    settings: Settings,
    output_file: str = "out.wav",
) -> str:
    """Run the full podcast generation pipeline.

    Flow:
        1. Read source markdown
        2. Sanitize for TTS consumption
        3. Build config-driven prompt
        4. Generate script (single LLM call)
        5. Normalize and validate speaker labels
        6. Chunk script at speaker-turn boundaries
        7. Synthesize audio per chunk
        8. Write combined WAV output

    Args:
        config: Pipeline configuration with hosts, style, and source file.
        settings: Application settings (API keys, etc.).
        output_file: Path for the output WAV file.

    Returns:
        The output file path.
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

    # 8. Write combined output
    write_wav(output_file, b"".join(audio_segments))
    logger.info("Saved podcast to %s", output_file)

    return output_file
