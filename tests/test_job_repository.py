"""Tests for JobRepository."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from src.domain.models import Job, JobState
from src.infrastructure.database.models import Base, HostRecord, PresetRecord, StyleRecord
from src.infrastructure.database.repositories import JobRepository


@pytest.fixture()
def session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    with factory() as s:
        s.add(HostRecord(name="Joe", voice="Kore", role="host"))
        s.add(HostRecord(name="Jane", voice="Puck", role="co-host"))
        s.add(StyleRecord(name="Default", tone="informative"))
        s.flush()
        s.add(PresetRecord(folder_path="/notes", host_a_id=1, host_b_id=2, style_id=1))
        s.flush()
        yield s


class TestJobRepository:
    def test_create_returns_job_with_id(self, session: Session):
        repo = JobRepository(session)
        j = repo.create(Job(source_file="note.md", preset_id=1))
        assert j.id is not None
        assert j.created_at is not None
        assert j.state == JobState.PENDING

    def test_get_by_id(self, session: Session):
        repo = JobRepository(session)
        created = repo.create(Job(source_file="note.md", preset_id=1))
        found = repo.get_by_id(created.id)
        assert found is not None
        assert found.source_file == "note.md"

    def test_get_next_pending_fifo(self, session: Session):
        repo = JobRepository(session)
        repo.create(Job(source_file="first.md", preset_id=1))
        repo.create(Job(source_file="second.md", preset_id=1))
        nxt = repo.get_next_pending()
        assert nxt is not None
        assert nxt.source_file == "first.md"

    def test_get_next_pending_none(self, session: Session):
        repo = JobRepository(session)
        assert repo.get_next_pending() is None

    def test_update_state_valid(self, session: Session):
        repo = JobRepository(session)
        j = repo.create(Job(source_file="note.md", preset_id=1))
        updated = repo.update_state(j.id, JobState.PROCESSING)
        assert updated.state == JobState.PROCESSING
        assert updated.started_at is not None

    def test_update_state_to_complete_sets_completed_at(self, session: Session):
        repo = JobRepository(session)
        j = repo.create(Job(source_file="note.md", preset_id=1))
        repo.update_state(j.id, JobState.PROCESSING)
        repo.update_state(j.id, JobState.ENCODING)
        repo.update_state(j.id, JobState.PUBLISHING)
        done = repo.update_state(j.id, JobState.COMPLETE)
        assert done.state == JobState.COMPLETE
        assert done.completed_at is not None

    def test_update_state_invalid_raises(self, session: Session):
        repo = JobRepository(session)
        j = repo.create(Job(source_file="note.md", preset_id=1))
        with pytest.raises(ValueError, match="Invalid state transition"):
            repo.update_state(j.id, JobState.ENCODING)  # pending -> encoding invalid

    def test_increment_retry(self, session: Session):
        repo = JobRepository(session)
        j = repo.create(Job(source_file="note.md", preset_id=1))
        updated = repo.increment_retry(j.id)
        assert updated.retry_count == 1
        updated2 = repo.increment_retry(j.id)
        assert updated2.retry_count == 2

    def test_mark_failed(self, session: Session):
        repo = JobRepository(session)
        j = repo.create(Job(source_file="note.md", preset_id=1))
        failed = repo.mark_failed(j.id, "Something broke")
        assert failed.state == JobState.FAILED
        assert failed.error_message == "Something broke"
        assert failed.completed_at is not None

    def test_get_interrupted_jobs(self, session: Session):
        repo = JobRepository(session)
        j1 = repo.create(Job(source_file="a.md", preset_id=1))
        j2 = repo.create(Job(source_file="b.md", preset_id=1))
        j3 = repo.create(Job(source_file="c.md", preset_id=1))
        repo.update_state(j1.id, JobState.PROCESSING)
        repo.update_state(j2.id, JobState.PROCESSING)
        repo.update_state(j2.id, JobState.ENCODING)
        # j3 stays pending -- not interrupted
        interrupted = repo.get_interrupted_jobs()
        assert len(interrupted) == 2
        states = {j.state for j in interrupted}
        assert states == {JobState.PROCESSING, JobState.ENCODING}

    def test_mark_failed_rejects_terminal_state(self, session: Session):
        repo = JobRepository(session)
        j = repo.create(Job(source_file="note.md", preset_id=1))
        repo.update_state(j.id, JobState.PROCESSING)
        repo.update_state(j.id, JobState.ENCODING)
        repo.update_state(j.id, JobState.PUBLISHING)
        repo.update_state(j.id, JobState.COMPLETE)
        with pytest.raises(ValueError, match="terminal state"):
            repo.mark_failed(j.id, "too late")

    def test_get_by_source_file_pending(self, session: Session):
        repo = JobRepository(session)
        repo.create(Job(source_file="note.md", preset_id=1))
        found = repo.get_by_source_file_pending("note.md")
        assert found is not None
        assert found.source_file == "note.md"

    def test_get_by_source_file_pending_none(self, session: Session):
        repo = JobRepository(session)
        assert repo.get_by_source_file_pending("nope.md") is None

    def test_get_by_source_file_pending_ignores_non_pending(self, session: Session):
        repo = JobRepository(session)
        j = repo.create(Job(source_file="note.md", preset_id=1))
        repo.update_state(j.id, JobState.PROCESSING)
        assert repo.get_by_source_file_pending("note.md") is None
