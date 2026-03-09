"""Sequential job processor with retry, state tracking, and cleanup."""

from __future__ import annotations

import logging
import os
import threading
from collections.abc import Callable

from sqlalchemy.orm import Session

from src.application.podcast_service import generate_podcast
from src.application.retry import retry_with_backoff
from src.config import Settings
from src.domain.models import Job, JobState, PipelineConfig
from src.exceptions import (
    PodcastError,
    ScriptGenerationError,
    TTSError,
)
from src.infrastructure.database.repositories import (
    HostRepository,
    JobRepository,
    PresetRepository,
    StyleRepository,
)

logger = logging.getLogger(__name__)


class JobProcessor:
    """Polls for pending jobs and drives each through the pipeline sequentially."""

    def __init__(
        self,
        settings: Settings,
        session_factory: Callable[[], Session],
        shutdown_event: threading.Event,
    ) -> None:
        self._settings = settings
        self._session_factory = session_factory
        self._shutdown_event = shutdown_event
        self._poll_interval = settings.job_poll_interval_seconds

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run(self) -> None:
        """Main loop -- call in a daemon thread."""
        self._recover_interrupted_jobs()

        while not self._shutdown_event.is_set():
            processed = False
            session = self._session_factory()
            try:
                job = JobRepository(session).get_next_pending()
                if job is not None:
                    self._process_job(job, session)
                    processed = True
            except Exception:
                logger.exception("Unexpected error in job processor loop")
                # If we have a job reference, mark it failed so it doesn't loop forever
                if job is not None:
                    try:
                        JobRepository(session).mark_failed(
                            job.id, "Unexpected processor error"
                        )
                        session.commit()
                    except Exception:
                        logger.exception("Failed to mark job %s as failed", job.id)
            finally:
                session.close()

            if processed:
                self._shutdown_event.wait(self._settings.job_cooldown_seconds)
            else:
                self._shutdown_event.wait(self._poll_interval)

    # ------------------------------------------------------------------
    # Recovery
    # ------------------------------------------------------------------

    def _recover_interrupted_jobs(self) -> None:
        """Re-queue jobs left in non-terminal active states from a previous run."""
        session = self._session_factory()
        try:
            repo = JobRepository(session)
            interrupted = repo.get_interrupted_jobs()
            for job in interrupted:
                # Reset to PENDING on the same record, preserving retry_count
                repo.update_state(job.id, JobState.PENDING)
                logger.info(
                    "Re-queued interrupted job %d (retry_count=%d)",
                    job.id, job.retry_count,
                )
            session.commit()
            if interrupted:
                logger.info("Recovered %d interrupted job(s)", len(interrupted))
        finally:
            session.close()

    # ------------------------------------------------------------------
    # Per-job processing
    # ------------------------------------------------------------------

    def _process_job(self, job: Job, session: Session) -> None:
        repo = JobRepository(session)
        job_id: int = job.id  # type: ignore[assignment]

        # --- Look up preset and related entities -----------------------
        preset = PresetRepository(session).get_by_id(job.preset_id)
        if preset is None:
            repo.mark_failed(job_id, "Preset not found")
            session.commit()
            return

        host_a = HostRepository(session).get_by_id(preset.host_a_id)
        host_b = HostRepository(session).get_by_id(preset.host_b_id)
        if host_a is None or host_b is None:
            repo.mark_failed(job_id, "Host not found for preset")
            session.commit()
            return

        style = StyleRepository(session).get_by_id(preset.style_id)
        if style is None:
            repo.mark_failed(job_id, "Style not found for preset")
            session.commit()
            return

        # Apply personality override from preset
        if preset.personality_guidance:
            style = style.model_copy(
                update={"personality_guidance": preset.personality_guidance},
            )

        config = PipelineConfig(
            hosts=[host_a, host_b],
            style=style,
            source_file=job.source_file,
        )

        # --- Transition to PROCESSING ---------------------------------
        repo.update_state(job_id, JobState.PROCESSING)
        session.commit()

        # --- Execute pipeline with retry ------------------------------
        try:

            def _run_pipeline() -> None:
                # Each retry attempt uses a fresh session to avoid stale state
                retry_session = self._session_factory()
                try:
                    generate_podcast(config, self._settings, retry_session)
                    retry_session.commit()
                except Exception:
                    retry_session.rollback()
                    raise
                finally:
                    retry_session.close()

            retry_with_backoff(
                fn=_run_pipeline,
                max_retries=self._settings.max_retries,
                backoff_initial=self._settings.backoff_initial_seconds,
                backoff_multiplier=self._settings.backoff_multiplier,
                backoff_max=self._settings.backoff_max_seconds,
                shutdown_event=self._shutdown_event,
            )

            # Transition through intermediate states to COMPLETE
            repo.update_state(job_id, JobState.ENCODING)
            repo.update_state(job_id, JobState.PUBLISHING)
            repo.update_state(job_id, JobState.COMPLETE)
            session.commit()
            logger.info("Job %d completed successfully", job_id)

        except InterruptedError:
            repo.mark_failed(job_id, "interrupted")
            session.commit()
            logger.info("Job %d interrupted by shutdown", job_id)

        except (ScriptGenerationError, TTSError) as exc:
            repo.increment_retry(job_id)
            repo.mark_failed(job_id, str(exc))
            session.commit()
            self._cleanup_partial_output(config)
            logger.warning("Job %d failed after retries: %s", job_id, exc)

        except PodcastError as exc:
            repo.mark_failed(job_id, str(exc))
            session.commit()
            self._cleanup_partial_output(config)
            logger.error("Job %d failed: %s", job_id, exc)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _cleanup_partial_output(self, config: PipelineConfig) -> None:
        """Remove orphaned MP3 files from a failed job."""
        from datetime import datetime, timezone
        from src.domain.models import sanitize_filename
        from src.infrastructure.reader import read_md_files
        from src.application.podcast_service import _extract_title

        try:
            content = read_md_files([config.source_file])
            title = _extract_title(content, config.source_file)
            today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            safe_title = sanitize_filename(title)
            filename = f"{today} - {safe_title}.mp3"
            path = os.path.join(self._settings.episodes_dir, filename)
            if os.path.exists(path):
                os.remove(path)
                logger.info("Cleaned up partial output: %s", path)
        except Exception:
            logger.debug("No partial output to clean up", exc_info=True)
