"""Integration tests for episode/job history dashboard routes."""

from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

from src.domain.models import Episode, Host, Job, JobState, Preset, Style
from src.infrastructure.database.repositories import (
    EpisodeRepository,
    HostRepository,
    JobRepository,
    PresetRepository,
    StyleRepository,
)


@pytest.fixture()
def _seed_episodes_and_jobs(db_session):
    """Seed completed episodes and jobs for testing the history view."""
    host_repo = HostRepository(db_session)
    style_repo = StyleRepository(db_session)
    preset_repo = PresetRepository(db_session)
    episode_repo = EpisodeRepository(db_session)
    job_repo = JobRepository(db_session)

    # Create hosts, style, and preset for job foreign key
    host_repo.create(Host(name="Joe", voice="Kore", role="host"))
    host_repo.create(Host(name="Jane", voice="Puck", role="co-host"))
    style_repo.create(Style(name="Default", tone="Informative"))
    preset_repo.create(
        Preset(folder_path="/vault/notes", host_a_id=1, host_b_id=2, style_id=1)
    )

    # Create 2 completed episodes
    episode_repo.create(
        Episode(
            title="First Episode",
            description="The very first episode",
            episode_number=1,
            filename="2026-03-01_first-episode.mp3",
            duration_seconds=300.0,
            file_size=5_000_000,
            hosts=["Joe", "Jane"],
            style_name="Default",
            source_file="notes/first.md",
            published_at=datetime(2026, 3, 1, 12, 0, 0, tzinfo=timezone.utc),
        )
    )
    episode_repo.create(
        Episode(
            title="Second Episode",
            description="The second episode",
            episode_number=2,
            filename="2026-03-05_second-episode.mp3",
            duration_seconds=600.0,
            file_size=10_000_000,
            hosts=["Joe", "Jane"],
            style_name="Default",
            source_file="notes/second.md",
            published_at=datetime(2026, 3, 5, 14, 0, 0, tzinfo=timezone.utc),
        )
    )

    # Create a failed job
    failed_job = job_repo.create(
        Job(
            source_file="notes/failed.md",
            preset_id=1,
            state=JobState.PENDING,
            created_at=datetime(2026, 3, 6, 10, 0, 0, tzinfo=timezone.utc),
        )
    )
    job_repo.update_state(failed_job.id, JobState.PROCESSING)
    job_repo.mark_failed(failed_job.id, "TTS API rate limit exceeded")
    job_repo.increment_retry(failed_job.id)

    # Create a pending job
    job_repo.create(
        Job(
            source_file="notes/pending.md",
            preset_id=1,
            state=JobState.PENDING,
            created_at=datetime(2026, 3, 7, 8, 0, 0, tzinfo=timezone.utc),
        )
    )

    db_session.commit()


class TestEpisodeList:
    """Tests for GET /dashboard/episodes."""

    def test_episode_list_returns_200(self, dashboard_client: TestClient, _seed_episodes_and_jobs):
        response = dashboard_client.get("/dashboard/episodes")
        assert response.status_code == 200

    def test_episode_list_shows_episode_data(self, dashboard_client: TestClient, _seed_episodes_and_jobs):
        response = dashboard_client.get("/dashboard/episodes")
        html = response.text
        assert "Second Episode" in html
        assert "First Episode" in html

    def test_episode_card_has_audio_player(self, dashboard_client: TestClient, _seed_episodes_and_jobs):
        response = dashboard_client.get("/dashboard/episodes")
        html = response.text
        assert "<audio" in html
        assert "/episodes/" in html

    def test_failed_job_shows_error(self, dashboard_client: TestClient, _seed_episodes_and_jobs):
        response = dashboard_client.get("/dashboard/episodes")
        html = response.text
        assert "TTS API rate limit exceeded" in html

    def test_episode_list_htmx_returns_partial(self, dashboard_client: TestClient, _seed_episodes_and_jobs):
        response = dashboard_client.get(
            "/dashboard/episodes",
            headers={"HX-Request": "true"},
        )
        assert response.status_code == 200
        assert "<!DOCTYPE" not in response.text

    def test_episode_list_requires_auth(self, dashboard_client: TestClient):
        client = TestClient(dashboard_client.app)
        response = client.get("/dashboard/episodes")
        assert response.status_code == 401


class TestEpisodeStatusFilter:
    """Tests for GET /dashboard/episodes?status=..."""

    def test_filter_complete_shows_only_episodes(self, dashboard_client: TestClient, _seed_episodes_and_jobs):
        response = dashboard_client.get("/dashboard/episodes?status=complete")
        html = response.text
        assert "First Episode" in html
        assert "Second Episode" in html
        assert "TTS API rate limit exceeded" not in html

    def test_filter_failed_shows_only_failed_jobs(self, dashboard_client: TestClient, _seed_episodes_and_jobs):
        response = dashboard_client.get("/dashboard/episodes?status=failed")
        html = response.text
        assert "failed.md" in html
        assert "TTS API rate limit exceeded" in html
        assert "First Episode" not in html

    def test_filter_in_progress_shows_pending_jobs(self, dashboard_client: TestClient, _seed_episodes_and_jobs):
        response = dashboard_client.get("/dashboard/episodes?status=in_progress")
        html = response.text
        assert "pending.md" in html
        assert "First Episode" not in html

    def test_filter_all_shows_everything(self, dashboard_client: TestClient, _seed_episodes_and_jobs):
        response = dashboard_client.get("/dashboard/episodes")
        html = response.text
        assert "First Episode" in html
        assert "failed.md" in html
        assert "pending.md" in html

    def test_filter_htmx_returns_partial(self, dashboard_client: TestClient, _seed_episodes_and_jobs):
        response = dashboard_client.get(
            "/dashboard/episodes?status=complete",
            headers={"HX-Request": "true"},
        )
        assert response.status_code == 200
        assert "<!DOCTYPE" not in response.text

    def test_filter_htmx_returns_cards_only_not_full_list(
        self, dashboard_client: TestClient, _seed_episodes_and_jobs
    ):
        """Filter requests must return card HTML only, not the heading/filters/wrapper."""
        response = dashboard_client.get(
            "/dashboard/episodes?status=complete",
            headers={"HX-Request": "true", "HX-Target": "episode-list"},
        )
        assert response.status_code == 200
        html = response.text
        # Must NOT contain the heading or filter bar (those are in list.html, not cards.html)
        assert "<h1>Episodes</h1>" not in html
        assert 'class="filter-bar"' not in html
        # Must NOT contain the wrapper div (that would cause nesting)
        assert 'id="episode-list"' not in html
        # Must contain actual episode content
        assert "First Episode" in html

    def test_sidebar_nav_returns_full_partial(
        self, dashboard_client: TestClient, _seed_episodes_and_jobs
    ):
        """Sidebar navigation (HX-Request but no HX-Target=episode-list) returns full list partial."""
        response = dashboard_client.get(
            "/dashboard/episodes",
            headers={"HX-Request": "true"},
        )
        assert response.status_code == 200
        html = response.text
        assert "<h1>Episodes</h1>" in html
        assert 'id="episode-list"' in html
