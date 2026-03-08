"""Tests for Phase 3 domain models: JobState, Preset, Job."""

import enum
from datetime import datetime

import pytest

from src.domain.models import Job, JobState, Preset


class TestJobState:
    """JobState enum behaviour."""

    def test_has_six_values(self):
        assert len(JobState) == 6

    def test_values(self):
        expected = {"pending", "processing", "encoding", "publishing", "complete", "failed"}
        assert {s.value for s in JobState} == expected

    def test_is_str_enum(self):
        assert isinstance(JobState.PENDING, str)

    def test_valid_transitions_pending(self):
        assert JobState.PENDING.valid_transitions() == {JobState.PROCESSING, JobState.FAILED}

    def test_valid_transitions_processing(self):
        assert JobState.PROCESSING.valid_transitions() == {JobState.ENCODING, JobState.FAILED}

    def test_valid_transitions_encoding(self):
        assert JobState.ENCODING.valid_transitions() == {JobState.PUBLISHING, JobState.FAILED}

    def test_valid_transitions_publishing(self):
        assert JobState.PUBLISHING.valid_transitions() == {JobState.COMPLETE, JobState.FAILED}

    def test_valid_transitions_complete_is_terminal(self):
        assert JobState.COMPLETE.valid_transitions() == set()

    def test_valid_transitions_failed_is_terminal(self):
        assert JobState.FAILED.valid_transitions() == set()


class TestPreset:
    """Preset domain model."""

    def test_create_minimal(self):
        p = Preset(folder_path="/notes/tech", host_a_id=1, host_b_id=2, style_id=1)
        assert p.id is None
        assert p.personality_guidance is None
        assert p.folder_path == "/notes/tech"

    def test_create_with_personality(self):
        p = Preset(
            folder_path="/notes/tech",
            host_a_id=1,
            host_b_id=2,
            style_id=1,
            personality_guidance="Be extra enthusiastic",
        )
        assert p.personality_guidance == "Be extra enthusiastic"


class TestJob:
    """Job domain model."""

    def test_defaults(self):
        j = Job(source_file="note.md", preset_id=1)
        assert j.id is None
        assert j.state == JobState.PENDING
        assert j.retry_count == 0
        assert j.error_message is None
        assert j.created_at is None
        assert j.started_at is None
        assert j.completed_at is None

    def test_explicit_state(self):
        j = Job(source_file="note.md", preset_id=1, state=JobState.PROCESSING)
        assert j.state == JobState.PROCESSING
