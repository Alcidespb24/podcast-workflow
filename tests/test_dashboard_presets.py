"""Integration tests for preset CRUD dashboard routes."""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from src.domain.models import Host, Preset, Style
from src.infrastructure.database.repositories import (
    HostRepository,
    PresetRepository,
    StyleRepository,
)


@pytest.fixture()
def _seed_hosts_and_styles(db_session):
    """Seed test hosts and styles into the database."""
    host_repo = HostRepository(db_session)
    style_repo = StyleRepository(db_session)
    host_repo.create(Host(name="Joe", voice="Kore", role="host"))
    host_repo.create(Host(name="Jane", voice="Puck", role="co-host"))
    style_repo.create(Style(name="Casual", tone="Relaxed and fun"))
    style_repo.create(Style(name="Formal", tone="Professional"))
    db_session.commit()


@pytest.fixture()
def _seed_preset(db_session, _seed_hosts_and_styles, dashboard_settings):
    """Seed a preset so list/edit/delete tests have data.

    Uses a path under vault_base_dir so path validation passes.
    """
    preset_repo = PresetRepository(db_session)
    valid_path = str(Path(dashboard_settings.vault_base_dir) / "notes")
    preset_repo.create(
        Preset(
            folder_path=valid_path,
            host_a_id=1,
            host_b_id=2,
            style_id=1,
            personality_guidance="Be friendly",
        )
    )
    db_session.commit()


class TestPresetList:
    """Tests for GET /dashboard/presets."""

    def test_preset_list_returns_200(self, dashboard_client: TestClient, _seed_hosts_and_styles):
        response = dashboard_client.get("/dashboard/presets")
        assert response.status_code == 200

    def test_preset_list_shows_preset_data(self, dashboard_client: TestClient, _seed_preset):
        response = dashboard_client.get("/dashboard/presets")
        assert response.status_code == 200
        html = response.text
        assert "notes" in html
        assert "Joe" in html
        assert "Jane" in html
        assert "Casual" in html

    def test_preset_list_htmx_returns_partial(self, dashboard_client: TestClient, _seed_hosts_and_styles):
        response = dashboard_client.get(
            "/dashboard/presets",
            headers={"HX-Request": "true"},
        )
        assert response.status_code == 200
        # Partial should NOT contain full HTML document
        assert "<!DOCTYPE" not in response.text

    def test_preset_list_requires_auth(self, dashboard_client: TestClient):
        client = TestClient(dashboard_client.app, follow_redirects=False)
        response = client.get("/dashboard/presets")
        assert response.status_code == 303
        assert "/login" in response.headers["location"]


class TestPresetCreate:
    """Tests for POST /dashboard/presets."""

    def test_create_preset_success(self, dashboard_client: TestClient, _seed_hosts_and_styles, dashboard_settings):
        valid_path = str(Path(dashboard_settings.vault_base_dir) / "tech")
        response = dashboard_client.post(
            "/dashboard/presets",
            data={
                "folder_path": valid_path,
                "host_a_id": "1",
                "host_b_id": "2",
                "style_id": "1",
                "personality_guidance": "Keep it technical",
            },
        )
        assert response.status_code == 200
        html = response.text
        assert "tech" in html

    def test_create_preset_missing_folder_path(self, dashboard_client: TestClient, _seed_hosts_and_styles):
        response = dashboard_client.post(
            "/dashboard/presets",
            data={
                "folder_path": "",
                "host_a_id": "1",
                "host_b_id": "2",
                "style_id": "1",
            },
        )
        assert response.status_code == 200
        assert "error" in response.text.lower() or "required" in response.text.lower()

    def test_create_preset_returns_toast(self, dashboard_client: TestClient, _seed_hosts_and_styles, dashboard_settings):
        valid_path = str(Path(dashboard_settings.vault_base_dir) / "new")
        response = dashboard_client.post(
            "/dashboard/presets",
            data={
                "folder_path": valid_path,
                "host_a_id": "1",
                "host_b_id": "2",
                "style_id": "1",
            },
        )
        assert response.status_code == 200
        assert "toast" in response.text

    def test_create_preset_requires_auth(self, dashboard_client: TestClient):
        client = TestClient(dashboard_client.app, follow_redirects=False)
        response = client.post(
            "/dashboard/presets",
            data={"folder_path": "/vault/x", "host_a_id": "1", "host_b_id": "2", "style_id": "1"},
        )
        assert response.status_code == 303
        assert "/login" in response.headers["location"]


class TestPresetNewForm:
    """Tests for GET /dashboard/presets/new."""

    def test_new_form_returns_200(self, dashboard_client: TestClient, _seed_hosts_and_styles):
        response = dashboard_client.get("/dashboard/presets/new")
        assert response.status_code == 200

    def test_new_form_has_select_elements(self, dashboard_client: TestClient, _seed_hosts_and_styles):
        response = dashboard_client.get("/dashboard/presets/new")
        html = response.text
        assert "<select" in html

    def test_new_form_has_host_options(self, dashboard_client: TestClient, _seed_hosts_and_styles):
        response = dashboard_client.get("/dashboard/presets/new")
        html = response.text
        assert "Joe" in html
        assert "Jane" in html

    def test_new_form_has_style_options(self, dashboard_client: TestClient, _seed_hosts_and_styles):
        response = dashboard_client.get("/dashboard/presets/new")
        html = response.text
        assert "Casual" in html
        assert "Formal" in html

    def test_new_form_has_vault_relative_placeholder(self, dashboard_client: TestClient, _seed_hosts_and_styles):
        response = dashboard_client.get("/dashboard/presets/new")
        html = response.text
        assert "Folder within vault" in html


class TestPresetEdit:
    """Tests for GET /dashboard/presets/{id}/edit."""

    def test_edit_form_returns_200(self, dashboard_client: TestClient, _seed_preset):
        response = dashboard_client.get("/dashboard/presets/1/edit")
        assert response.status_code == 200

    def test_edit_form_has_current_values(self, dashboard_client: TestClient, _seed_preset):
        response = dashboard_client.get("/dashboard/presets/1/edit")
        html = response.text
        assert "notes" in html
        assert "Be friendly" in html

    def test_edit_form_returns_404_for_missing(self, dashboard_client: TestClient, _seed_hosts_and_styles):
        response = dashboard_client.get("/dashboard/presets/999/edit")
        assert response.status_code == 404


class TestPresetUpdate:
    """Tests for PUT /dashboard/presets/{id}."""

    def test_update_preset_success(self, dashboard_client: TestClient, _seed_preset, dashboard_settings):
        valid_path = str(Path(dashboard_settings.vault_base_dir) / "updated")
        response = dashboard_client.put(
            "/dashboard/presets/1",
            data={
                "folder_path": valid_path,
                "host_a_id": "2",
                "host_b_id": "1",
                "style_id": "2",
                "personality_guidance": "Updated guidance",
            },
        )
        assert response.status_code == 200
        html = response.text
        assert "updated" in html

    def test_update_preset_returns_toast(self, dashboard_client: TestClient, _seed_preset, dashboard_settings):
        valid_path = str(Path(dashboard_settings.vault_base_dir) / "updated")
        response = dashboard_client.put(
            "/dashboard/presets/1",
            data={
                "folder_path": valid_path,
                "host_a_id": "1",
                "host_b_id": "2",
                "style_id": "1",
            },
        )
        assert response.status_code == 200
        assert "toast" in response.text

    def test_update_preset_returns_404_for_missing(self, dashboard_client: TestClient, _seed_hosts_and_styles):
        response = dashboard_client.put(
            "/dashboard/presets/999",
            data={"folder_path": "/vault/x", "host_a_id": "1", "host_b_id": "2", "style_id": "1"},
        )
        assert response.status_code == 404


class TestPresetDelete:
    """Tests for DELETE /dashboard/presets/{id}."""

    def test_delete_preset_success(self, dashboard_client: TestClient, _seed_preset):
        response = dashboard_client.request("DELETE", "/dashboard/presets/1")
        assert response.status_code == 200
        assert "toast" in response.text

    def test_delete_preset_removes_from_list(self, dashboard_client: TestClient, _seed_preset):
        dashboard_client.request("DELETE", "/dashboard/presets/1")
        response = dashboard_client.get("/dashboard/presets")
        assert "notes" not in response.text

    def test_delete_preset_returns_404_for_missing(self, dashboard_client: TestClient, _seed_hosts_and_styles):
        response = dashboard_client.request("DELETE", "/dashboard/presets/999")
        assert response.status_code == 404


class TestPresetPathValidation:
    """Tests for path traversal rejection on preset create/update."""

    def test_create_preset_traversal_rejected(self, dashboard_client: TestClient, _seed_hosts_and_styles):
        """POST with traversal path returns 422."""
        response = dashboard_client.post(
            "/dashboard/presets",
            data={
                "folder_path": "../../../etc",
                "host_a_id": "1",
                "host_b_id": "2",
                "style_id": "1",
            },
        )
        assert response.status_code == 422

    def test_update_preset_traversal_rejected(self, dashboard_client: TestClient, _seed_preset):
        """PUT with traversal path returns 422."""
        response = dashboard_client.put(
            "/dashboard/presets/1",
            data={
                "folder_path": "../../../etc",
                "host_a_id": "1",
                "host_b_id": "2",
                "style_id": "1",
            },
        )
        assert response.status_code == 422

    def test_create_preset_valid_path_succeeds(self, dashboard_client: TestClient, _seed_hosts_and_styles, dashboard_settings):
        """POST with path under vault_base_dir returns 200."""
        valid_path = str(Path(dashboard_settings.vault_base_dir) / "valid_folder")
        response = dashboard_client.post(
            "/dashboard/presets",
            data={
                "folder_path": valid_path,
                "host_a_id": "1",
                "host_b_id": "2",
                "style_id": "1",
            },
        )
        assert response.status_code == 200

    def test_traversal_error_message_generic(self, dashboard_client: TestClient, _seed_hosts_and_styles):
        """422 response body contains generic error, not real paths."""
        response = dashboard_client.post(
            "/dashboard/presets",
            data={
                "folder_path": "../../../etc",
                "host_a_id": "1",
                "host_b_id": "2",
                "style_id": "1",
            },
        )
        assert response.status_code == 422
        assert "Path must be within the vault directory" in response.text

    def test_preset_list_shows_warning_badge(self, dashboard_client: TestClient, _seed_hosts_and_styles, db_session):
        """Preset with out-of-bounds path shows warning badge in list."""
        # Insert a preset with an invalid path directly in DB (bypassing validation)
        preset_repo = PresetRepository(db_session)
        preset_repo.create(
            Preset(
                folder_path="/definitely/outside/vault",
                host_a_id=1,
                host_b_id=2,
                style_id=1,
            )
        )
        db_session.commit()
        response = dashboard_client.get("/dashboard/presets")
        assert response.status_code == 200
        assert "Invalid path" in response.text

    def test_inline_error_element_present(self, dashboard_client: TestClient, _seed_hosts_and_styles):
        """Form has a folder-path-error target element."""
        response = dashboard_client.get("/dashboard/presets/new")
        assert 'id="folder-path-error"' in response.text
