"""Repository classes that map ORM records to domain models."""

import json
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from src.config import Settings
from src.domain.models import Episode, Host, Job, JobState, Preset, Style
from src.infrastructure.database.models import (
    EpisodeRecord,
    HostRecord,
    JobRecord,
    PresetRecord,
    StyleRecord,
)

# Columns that are safe to update via the generic update() method.
_HOST_MUTABLE_FIELDS = frozenset({"name", "voice", "role", "is_default"})
_STYLE_MUTABLE_FIELDS = frozenset({"name", "tone", "personality_guidance", "is_default"})


class HostRepository:
    """CRUD operations for hosts, returning domain models."""

    def __init__(self, session: Session) -> None:
        self._session = session

    @staticmethod
    def _to_domain(record: HostRecord) -> Host:
        return Host(
            id=record.id,
            name=record.name,
            voice=record.voice,
            role=record.role,
        )

    def create(self, host: Host) -> Host:
        record = HostRecord(
            name=host.name,
            voice=host.voice,
            role=host.role,
        )
        self._session.add(record)
        self._session.flush()
        return self._to_domain(record)

    def get_by_id(self, host_id: int) -> Host | None:
        record = self._session.get(HostRecord, host_id)
        if record is None:
            return None
        return self._to_domain(record)

    def get_all(self) -> list[Host]:
        stmt = select(HostRecord).order_by(HostRecord.id)
        return [self._to_domain(r) for r in self._session.scalars(stmt)]

    def get_defaults(self) -> list[Host]:
        stmt = select(HostRecord).where(HostRecord.is_default.is_(True)).order_by(HostRecord.id)
        return [self._to_domain(r) for r in self._session.scalars(stmt)]

    def update(self, host_id: int, **fields: Any) -> Host | None:
        record = self._session.get(HostRecord, host_id)
        if record is None:
            return None
        unknown = fields.keys() - _HOST_MUTABLE_FIELDS
        if unknown:
            raise ValueError(f"Unknown Host fields: {unknown}")
        for key, value in fields.items():
            setattr(record, key, value)
        self._session.flush()
        return self._to_domain(record)

    def delete(self, host_id: int) -> bool:
        record = self._session.get(HostRecord, host_id)
        if record is None:
            return False
        self._session.delete(record)
        self._session.flush()
        return True


class StyleRepository:
    """CRUD operations for styles, returning domain models."""

    def __init__(self, session: Session) -> None:
        self._session = session

    @staticmethod
    def _to_domain(record: StyleRecord) -> Style:
        return Style(
            id=record.id,
            name=record.name,
            tone=record.tone,
            personality_guidance=record.personality_guidance,
        )

    def create(self, style: Style) -> Style:
        record = StyleRecord(
            name=style.name,
            tone=style.tone,
            personality_guidance=style.personality_guidance,
        )
        self._session.add(record)
        self._session.flush()
        return self._to_domain(record)

    def get_by_id(self, style_id: int) -> Style | None:
        record = self._session.get(StyleRecord, style_id)
        if record is None:
            return None
        return self._to_domain(record)

    def get_all(self) -> list[Style]:
        stmt = select(StyleRecord).order_by(StyleRecord.id)
        return [self._to_domain(r) for r in self._session.scalars(stmt)]

    def get_defaults(self) -> list[Style]:
        stmt = select(StyleRecord).where(StyleRecord.is_default.is_(True)).order_by(StyleRecord.id)
        return [self._to_domain(r) for r in self._session.scalars(stmt)]

    def update(self, style_id: int, **fields: Any) -> Style | None:
        record = self._session.get(StyleRecord, style_id)
        if record is None:
            return None
        unknown = fields.keys() - _STYLE_MUTABLE_FIELDS
        if unknown:
            raise ValueError(f"Unknown Style fields: {unknown}")
        for key, value in fields.items():
            setattr(record, key, value)
        self._session.flush()
        return self._to_domain(record)

    def delete(self, style_id: int) -> bool:
        record = self._session.get(StyleRecord, style_id)
        if record is None:
            return False
        self._session.delete(record)
        self._session.flush()
        return True


class EpisodeRepository:
    """CRUD operations for episodes, returning domain models."""

    def __init__(self, session: Session) -> None:
        self._session = session

    @staticmethod
    def _to_domain(record: EpisodeRecord) -> Episode:
        return Episode(
            id=record.id,
            title=record.title,
            description=record.description,
            episode_number=record.episode_number,
            filename=record.filename,
            duration_seconds=record.duration_seconds,
            file_size=record.file_size,
            hosts=json.loads(record.hosts_json),
            style_name=record.style_name,
            source_file=record.source_file,
            published_at=record.published_at,
        )

    def create(self, episode: Episode) -> Episode:
        record = EpisodeRecord(
            title=episode.title,
            description=episode.description,
            episode_number=episode.episode_number,
            filename=episode.filename,
            duration_seconds=episode.duration_seconds,
            file_size=episode.file_size,
            hosts_json=json.dumps(episode.hosts),
            style_name=episode.style_name,
            source_file=episode.source_file,
            published_at=episode.published_at,
        )
        self._session.add(record)
        self._session.flush()
        return self._to_domain(record)

    def get_by_id(self, episode_id: int) -> Episode | None:
        record = self._session.get(EpisodeRecord, episode_id)
        if record is None:
            return None
        return self._to_domain(record)

    def get_all(self) -> list[Episode]:
        stmt = select(EpisodeRecord).order_by(EpisodeRecord.episode_number.desc())
        return [self._to_domain(r) for r in self._session.scalars(stmt)]

    def get_next_episode_number(self) -> int:
        max_num = self._session.scalar(
            select(func.max(EpisodeRecord.episode_number))
        )
        if max_num is None:
            return 1
        return max_num + 1


class PresetRepository:
    """CRUD operations for presets, returning domain models."""

    def __init__(self, session: Session) -> None:
        self._session = session

    @staticmethod
    def _to_domain(record: PresetRecord) -> Preset:
        return Preset(
            id=record.id,
            folder_path=record.folder_path,
            host_a_id=record.host_a_id,
            host_b_id=record.host_b_id,
            style_id=record.style_id,
            personality_guidance=record.personality_guidance,
        )

    def create(self, preset: Preset) -> Preset:
        record = PresetRecord(
            folder_path=preset.folder_path,
            host_a_id=preset.host_a_id,
            host_b_id=preset.host_b_id,
            style_id=preset.style_id,
            personality_guidance=preset.personality_guidance,
        )
        self._session.add(record)
        self._session.flush()
        return self._to_domain(record)

    def get_by_id(self, preset_id: int) -> Preset | None:
        record = self._session.get(PresetRecord, preset_id)
        if record is None:
            return None
        return self._to_domain(record)

    def get_by_folder_path(self, folder_path: str) -> Preset | None:
        stmt = select(PresetRecord).where(PresetRecord.folder_path == folder_path)
        record = self._session.scalar(stmt)
        if record is None:
            return None
        return self._to_domain(record)

    def get_all(self) -> list[Preset]:
        stmt = select(PresetRecord).order_by(PresetRecord.id)
        return [self._to_domain(r) for r in self._session.scalars(stmt)]

    def delete(self, preset_id: int) -> bool:
        record = self._session.get(PresetRecord, preset_id)
        if record is None:
            return False
        self._session.delete(record)
        self._session.flush()
        return True


class JobRepository:
    """CRUD and state-management operations for jobs."""

    def __init__(self, session: Session) -> None:
        self._session = session

    @staticmethod
    def _to_domain(record: JobRecord) -> Job:
        return Job(
            id=record.id,
            source_file=record.source_file,
            preset_id=record.preset_id,
            state=JobState(record.state),
            error_message=record.error_message,
            retry_count=record.retry_count,
            created_at=record.created_at,
            started_at=record.started_at,
            completed_at=record.completed_at,
        )

    def create(self, job: Job) -> Job:
        record = JobRecord(
            source_file=job.source_file,
            preset_id=job.preset_id,
            state=job.state.value,
            error_message=job.error_message,
            retry_count=job.retry_count,
        )
        if job.created_at is None:
            record.created_at = datetime.now(timezone.utc)
        else:
            record.created_at = job.created_at
        self._session.add(record)
        self._session.flush()
        return self._to_domain(record)

    def get_by_id(self, job_id: int) -> Job | None:
        record = self._session.get(JobRecord, job_id)
        if record is None:
            return None
        return self._to_domain(record)

    def get_next_pending(self) -> Job | None:
        stmt = (
            select(JobRecord)
            .where(JobRecord.state == JobState.PENDING.value)
            .order_by(JobRecord.created_at.asc())
            .limit(1)
        )
        record = self._session.scalar(stmt)
        if record is None:
            return None
        return self._to_domain(record)

    def update_state(self, job_id: int, new_state: JobState) -> Job:
        record = self._session.get(JobRecord, job_id)
        if record is None:
            raise ValueError(f"Job {job_id} not found")
        current = JobState(record.state)
        if new_state not in current.valid_transitions():
            raise ValueError(
                f"Invalid state transition: {current.value} -> {new_state.value}"
            )
        record.state = new_state.value
        now = datetime.now(timezone.utc)
        if new_state == JobState.PROCESSING:
            record.started_at = now
        if new_state in (JobState.COMPLETE, JobState.FAILED):
            record.completed_at = now
        self._session.flush()
        return self._to_domain(record)

    def increment_retry(self, job_id: int) -> Job:
        record = self._session.get(JobRecord, job_id)
        if record is None:
            raise ValueError(f"Job {job_id} not found")
        record.retry_count += 1
        self._session.flush()
        return self._to_domain(record)

    def mark_failed(self, job_id: int, error_message: str) -> Job:
        record = self._session.get(JobRecord, job_id)
        if record is None:
            raise ValueError(f"Job {job_id} not found")
        current = JobState(record.state)
        if JobState.FAILED not in current.valid_transitions():
            raise ValueError(
                f"Cannot mark job as failed from terminal state: {current.value}"
            )
        record.state = JobState.FAILED.value
        record.error_message = error_message
        record.completed_at = datetime.now(timezone.utc)
        self._session.flush()
        return self._to_domain(record)

    def get_interrupted_jobs(self) -> list[Job]:
        interrupted_states = [
            JobState.PROCESSING.value,
            JobState.ENCODING.value,
            JobState.PUBLISHING.value,
        ]
        stmt = select(JobRecord).where(JobRecord.state.in_(interrupted_states))
        return [self._to_domain(r) for r in self._session.scalars(stmt)]

    def get_by_source_file_pending(self, source_file: str) -> Job | None:
        stmt = (
            select(JobRecord)
            .where(JobRecord.source_file == source_file)
            .where(JobRecord.state == JobState.PENDING.value)
            .limit(1)
        )
        record = self._session.scalar(stmt)
        if record is None:
            return None
        return self._to_domain(record)


def seed_defaults(session: Session, settings: Settings) -> None:
    """Insert default hosts and style if the tables are empty. Idempotent."""
    host_count = session.scalar(select(HostRecord.id).limit(1))
    if host_count is None:
        session.add(
            HostRecord(
                name=settings.default_host_a_name,
                voice=settings.default_host_a_voice,
                role="host",
                is_default=True,
            )
        )
        session.add(
            HostRecord(
                name=settings.default_host_b_name,
                voice=settings.default_host_b_voice,
                role="co-host",
                is_default=True,
            )
        )

    style_count = session.scalar(select(StyleRecord.id).limit(1))
    if style_count is None:
        session.add(
            StyleRecord(
                name="Default",
                tone=settings.default_style_tone,
                is_default=True,
            )
        )

    session.flush()
