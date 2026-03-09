"""WatcherService -- manages watchdog Observer and JobProcessor lifecycle."""

from __future__ import annotations

import logging
import os
import threading
from collections.abc import Callable

from watchdog.observers import Observer

from sqlalchemy.orm import Session

from src.application.job_processor import JobProcessor
from src.backend.watcher.handler import DebouncedMarkdownHandler
from src.config import Settings
from src.domain.models import Job
from src.infrastructure.database.repositories import JobRepository, PresetRepository

logger = logging.getLogger(__name__)


class WatcherService:
    """Manages folder observers and the background job processor."""

    def __init__(
        self,
        settings: Settings,
        session_factory: Callable[[], Session],
    ) -> None:
        self._settings = settings
        self._session_factory = session_factory
        self._shutdown_event = threading.Event()
        self._job_processor = JobProcessor(settings, session_factory, self._shutdown_event)
        self._observer: Observer | None = None
        self._processor_thread: threading.Thread | None = None
        self._handlers: list[DebouncedMarkdownHandler] = []

    @property
    def is_running(self) -> bool:
        """Whether the watcher observer is currently running."""
        return self._observer is not None and self._observer.is_alive()

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def start(self) -> None:
        """Start watching preset folders and processing jobs."""
        session = self._session_factory()
        try:
            presets = PresetRepository(session).get_all()
        finally:
            session.close()

        if not presets:
            logger.warning("No folder presets configured -- watcher has nothing to watch")
            return

        self._observer = Observer()

        for preset in presets:
            # Ensure the watched directory exists
            os.makedirs(preset.folder_path, exist_ok=True)
            handler = DebouncedMarkdownHandler(
                on_file_ready=self._on_file_ready,
                debounce_seconds=self._settings.watcher_debounce_seconds,
            )
            self._handlers.append(handler)
            self._observer.schedule(handler, preset.folder_path, recursive=False)

        self._observer.start()

        self._processor_thread = threading.Thread(
            target=self._job_processor.run,
            daemon=True,
        )
        self._processor_thread.start()

        logger.info("Watcher started, monitoring %d folder(s)", len(presets))

    def stop(self) -> None:
        """Signal shutdown and wait for threads to finish."""
        self._shutdown_event.set()

        for handler in self._handlers:
            handler.cleanup()
        self._handlers.clear()

        if self._observer is not None:
            self._observer.stop()
            self._observer.join(timeout=5.0)
            if self._observer.is_alive():
                logger.warning("Observer thread did not stop within timeout")
            self._observer = None

        if self._processor_thread is not None:
            self._processor_thread.join(timeout=10.0)
            if self._processor_thread.is_alive():
                logger.warning("Processor thread did not stop within timeout")
            self._processor_thread = None

        logger.info("Watcher stopped")

    # ------------------------------------------------------------------
    # File callback
    # ------------------------------------------------------------------

    def _on_file_ready(self, file_path: str) -> None:
        """Called by debounced handler when a .md file stabilizes."""
        session = self._session_factory()
        try:
            parent_dir = os.path.normpath(os.path.dirname(file_path))
            preset = PresetRepository(session).get_by_folder_path(parent_dir)
            if preset is None:
                logger.warning("No preset for folder %s -- ignoring %s", parent_dir, file_path)
                return

            # Dedup: skip if already queued
            existing = JobRepository(session).get_by_source_file_pending(file_path)
            if existing is not None:
                logger.info("Job already queued for %s -- skipping", file_path)
                return

            job = Job(source_file=file_path, preset_id=preset.id)  # type: ignore[arg-type]
            JobRepository(session).create(job)
            session.commit()
            logger.info("Enqueued job for %s", file_path)
        except Exception:
            session.rollback()
            logger.exception("Failed to enqueue job for %s", file_path)
        finally:
            session.close()
