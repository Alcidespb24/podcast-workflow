"""Batch processor — scan preset folders, queue new files, process all, exit.

Designed to run as a scheduled task (e.g. Windows Task Scheduler at 8:30 AM).
Processes every unqueued .md file found in preset watch folders, then exits.
"""

import logging
import os
import threading
from pathlib import Path

from sqlalchemy import select

from src.config import load_settings
from src.domain.models import Job
from src.domain.path_validator import validate_path_within
from src.exceptions import PathTraversalError
from src.infrastructure.database import create_db_engine, get_session_factory, run_migrations
from src.infrastructure.database.models import JobRecord
from src.infrastructure.database.repositories import (
    JobRepository,
    PresetRepository,
    seed_defaults,
)
from src.application.job_processor import JobProcessor

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("batch_process")


def main() -> None:
    settings = load_settings()

    Path("data").mkdir(exist_ok=True)
    run_migrations(settings.database_url)
    engine = create_db_engine(settings.database_url)
    session_factory = get_session_factory(engine)

    with session_factory() as session:
        seed_defaults(session, settings)
        session.commit()

    # 1. Scan preset folders for new .md files
    queued = 0
    with session_factory() as session:
        presets = PresetRepository(session).get_all()
        if not presets:
            logger.info("No presets configured — nothing to process.")
            return

        for preset in presets:
            try:
                validate_path_within(preset.folder_path, settings.vault_base_dir)
            except PathTraversalError:
                logger.warning("Preset %d folder outside vault, skipping: %s", preset.id, preset.folder_path)
                continue

            if not os.path.isdir(preset.folder_path):
                logger.warning("Preset folder missing, skipping: %s", preset.folder_path)
                continue

            for entry in os.scandir(preset.folder_path):
                if not entry.name.endswith(".md") or not entry.is_file():
                    continue

                file_path = os.path.normpath(entry.path)

                # Skip if any job already exists for this file (any state)
                existing = session.scalar(
                    select(JobRecord.id).where(JobRecord.source_file == file_path).limit(1)
                )
                if existing is not None:
                    continue

                job = Job(source_file=file_path, preset_id=preset.id)
                JobRepository(session).create(job)
                queued += 1
                logger.info("Queued: %s", file_path)

        session.commit()

    if queued == 0:
        logger.info("No new files to process.")
        return

    logger.info("Queued %d file(s). Processing...", queued)

    # 2. Process all pending jobs, then exit
    shutdown = threading.Event()
    processor = JobProcessor(settings, session_factory, shutdown)
    processor._recover_interrupted_jobs()

    while True:
        with session_factory() as session:
            job = JobRepository(session).get_next_pending()
            if job is None:
                break
            processor._process_job(job, session)

    logger.info("Batch complete.")


if __name__ == "__main__":
    main()
