"""Tests for Episode domain model and EpisodeRepository."""

from datetime import datetime, timezone

import pytest

from src.domain.models import Episode, sanitize_filename
from src.infrastructure.database.repositories import EpisodeRepository


# -- Episode domain model tests --


class TestEpisodeDurationStr:
    """Episode.duration_str formats seconds as MM:SS or H:MM:SS."""

    def test_minutes_and_seconds(self, sample_episode: Episode) -> None:
        ep = sample_episode.model_copy(update={"duration_seconds": 125.5})
        assert ep.duration_str == "2:05"

    def test_exact_minute(self, sample_episode: Episode) -> None:
        ep = sample_episode.model_copy(update={"duration_seconds": 60.0})
        assert ep.duration_str == "1:00"

    def test_over_one_hour(self, sample_episode: Episode) -> None:
        ep = sample_episode.model_copy(update={"duration_seconds": 3661.0})
        assert ep.duration_str == "1:01:01"

    def test_zero_seconds(self, sample_episode: Episode) -> None:
        ep = sample_episode.model_copy(update={"duration_seconds": 0.0})
        assert ep.duration_str == "0:00"


class TestSanitizeFilename:
    """sanitize_filename strips illegal chars, trailing dots/spaces, and limits length."""

    def test_strips_illegal_chars(self) -> None:
        assert sanitize_filename('my<>:"/\\|?*file') == "myfile"

    def test_strips_trailing_dots_and_spaces(self) -> None:
        assert sanitize_filename("hello...  ") == "hello"

    def test_limits_length(self) -> None:
        long_name = "a" * 300
        result = sanitize_filename(long_name, max_length=200)
        assert len(result) == 200

    def test_preserves_valid_chars(self) -> None:
        assert sanitize_filename("my-podcast_episode 01") == "my-podcast_episode 01"


# -- EpisodeRepository tests --


class TestEpisodeRepositoryCreate:
    """EpisodeRepository.create() persists and returns Episode with id."""

    def test_create_returns_episode_with_id(self, db_session, sample_episode: Episode) -> None:
        repo = EpisodeRepository(db_session)
        created = repo.create(sample_episode)
        assert created.id is not None
        assert created.title == "Test Episode"
        assert created.hosts == ["Joe", "Jane"]

    def test_create_persists_all_fields(self, db_session, sample_episode: Episode) -> None:
        repo = EpisodeRepository(db_session)
        created = repo.create(sample_episode)
        fetched = repo.get_by_id(created.id)
        assert fetched is not None
        assert fetched.title == sample_episode.title
        assert fetched.description == sample_episode.description
        assert fetched.episode_number == sample_episode.episode_number
        assert fetched.filename == sample_episode.filename
        assert fetched.duration_seconds == pytest.approx(sample_episode.duration_seconds)
        assert fetched.file_size == sample_episode.file_size
        assert fetched.hosts == sample_episode.hosts
        assert fetched.style_name == sample_episode.style_name
        assert fetched.source_file == sample_episode.source_file


class TestEpisodeRepositoryGetById:
    """EpisodeRepository.get_by_id() returns Episode or None."""

    def test_returns_none_for_missing_id(self, db_session) -> None:
        repo = EpisodeRepository(db_session)
        assert repo.get_by_id(999) is None

    def test_returns_episode_for_existing_id(self, db_session, sample_episode: Episode) -> None:
        repo = EpisodeRepository(db_session)
        created = repo.create(sample_episode)
        fetched = repo.get_by_id(created.id)
        assert fetched is not None
        assert fetched.id == created.id


class TestEpisodeRepositoryGetAll:
    """EpisodeRepository.get_all() returns episodes ordered by episode_number desc."""

    def test_empty_returns_empty_list(self, db_session) -> None:
        repo = EpisodeRepository(db_session)
        assert repo.get_all() == []

    def test_ordered_by_episode_number_descending(self, db_session, sample_episode: Episode) -> None:
        repo = EpisodeRepository(db_session)
        ep1 = sample_episode.model_copy(update={"episode_number": 1, "title": "First"})
        ep2 = sample_episode.model_copy(update={"episode_number": 2, "title": "Second"})
        ep3 = sample_episode.model_copy(update={"episode_number": 3, "title": "Third"})
        repo.create(ep1)
        repo.create(ep2)
        repo.create(ep3)
        episodes = repo.get_all()
        assert len(episodes) == 3
        assert episodes[0].episode_number == 3
        assert episodes[1].episode_number == 2
        assert episodes[2].episode_number == 1


class TestEpisodeRepositoryGetNextEpisodeNumber:
    """EpisodeRepository.get_next_episode_number() returns max+1 or 1 if empty."""

    def test_returns_1_when_no_episodes(self, db_session) -> None:
        repo = EpisodeRepository(db_session)
        assert repo.get_next_episode_number() == 1

    def test_returns_max_plus_1(self, db_session, sample_episode: Episode) -> None:
        repo = EpisodeRepository(db_session)
        repo.create(sample_episode.model_copy(update={"episode_number": 5}))
        repo.create(sample_episode.model_copy(update={"episode_number": 3}))
        assert repo.get_next_episode_number() == 6
