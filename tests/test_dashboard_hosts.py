"""Integration tests for Host CRUD dashboard routes."""

import base64

import pytest
from fastapi.testclient import TestClient

from src.domain.models import Host
from src.infrastructure.database.repositories import HostRepository


AUTH_HEADER = f"Basic {base64.b64encode(b'admin:testpass').decode('ascii')}"


def _seed_host(dashboard_client: TestClient, name: str = "Alice", voice: str = "Kore", role: str = "host") -> None:
    """Create a host via the session_factory for test seeding."""
    sf = dashboard_client.app.state.session_factory
    session = sf()
    try:
        repo = HostRepository(session)
        repo.create(Host(name=name, voice=voice, role=role))
        session.commit()
    finally:
        session.close()


class TestHostList:
    """Tests for GET /dashboard/hosts."""

    def test_returns_200_with_auth(self, dashboard_client: TestClient):
        response = dashboard_client.get("/dashboard/hosts")
        assert response.status_code == 200

    def test_contains_hosts_heading(self, dashboard_client: TestClient):
        response = dashboard_client.get("/dashboard/hosts")
        assert "Hosts" in response.text

    def test_htmx_request_returns_partial(self, dashboard_client: TestClient):
        response = dashboard_client.get(
            "/dashboard/hosts",
            headers={"HX-Request": "true"},
        )
        assert response.status_code == 200
        # Partial should NOT contain the full page structure
        assert "<!DOCTYPE html>" not in response.text
        assert "Hosts" in response.text

    def test_full_request_returns_page_with_sidebar(self, dashboard_client: TestClient):
        response = dashboard_client.get("/dashboard/hosts")
        assert response.status_code == 200
        assert "<!DOCTYPE html>" in response.text
        assert "sidebar" in response.text

    def test_lists_seeded_hosts(self, dashboard_client: TestClient):
        _seed_host(dashboard_client, name="Alice", voice="Kore", role="host")
        _seed_host(dashboard_client, name="Bob", voice="Puck", role="co-host")
        response = dashboard_client.get(
            "/dashboard/hosts",
            headers={"HX-Request": "true"},
        )
        assert "Alice" in response.text
        assert "Bob" in response.text

    def test_returns_401_without_auth(self, dashboard_client: TestClient):
        # Remove auth header
        client = TestClient(dashboard_client.app)
        response = client.get("/dashboard/hosts")
        assert response.status_code == 401


class TestHostCreate:
    """Tests for POST /dashboard/hosts."""

    def test_create_host_returns_updated_list(self, dashboard_client: TestClient):
        response = dashboard_client.post(
            "/dashboard/hosts",
            data={"name": "NewHost", "voice": "Kore", "role": "host"},
        )
        assert response.status_code == 200
        assert "NewHost" in response.text

    def test_create_host_returns_toast(self, dashboard_client: TestClient):
        response = dashboard_client.post(
            "/dashboard/hosts",
            data={"name": "ToastHost", "voice": "Puck", "role": "co-host"},
        )
        assert "toast" in response.text
        assert "created" in response.text.lower()

    def test_create_host_missing_name_returns_422(self, dashboard_client: TestClient):
        response = dashboard_client.post(
            "/dashboard/hosts",
            data={"name": "", "voice": "Kore", "role": "host"},
        )
        assert response.status_code == 422

    def test_create_host_requires_auth(self, dashboard_client: TestClient):
        client = TestClient(dashboard_client.app)
        response = client.post(
            "/dashboard/hosts",
            data={"name": "NoAuth", "voice": "Kore", "role": "host"},
        )
        assert response.status_code == 401


class TestHostEdit:
    """Tests for GET /dashboard/hosts/{id}/edit."""

    def test_edit_form_loads_with_host_data(self, dashboard_client: TestClient):
        _seed_host(dashboard_client, name="EditMe", voice="Kore", role="host")
        # Get the host ID
        sf = dashboard_client.app.state.session_factory
        session = sf()
        try:
            repo = HostRepository(session)
            hosts = repo.get_all()
            host_id = hosts[0].id
        finally:
            session.close()

        response = dashboard_client.get(f"/dashboard/hosts/{host_id}/edit")
        assert response.status_code == 200
        assert "EditMe" in response.text
        assert "dialog" in response.text.lower()


class TestHostUpdate:
    """Tests for PUT /dashboard/hosts/{id}."""

    def test_update_host_returns_updated_list(self, dashboard_client: TestClient):
        _seed_host(dashboard_client, name="OldName", voice="Kore", role="host")
        sf = dashboard_client.app.state.session_factory
        session = sf()
        try:
            repo = HostRepository(session)
            hosts = repo.get_all()
            host_id = hosts[0].id
        finally:
            session.close()

        response = dashboard_client.put(
            f"/dashboard/hosts/{host_id}",
            data={"name": "UpdatedName", "voice": "Puck", "role": "co-host"},
        )
        assert response.status_code == 200
        assert "UpdatedName" in response.text

    def test_update_host_returns_toast(self, dashboard_client: TestClient):
        _seed_host(dashboard_client, name="ToastUpdate", voice="Kore", role="host")
        sf = dashboard_client.app.state.session_factory
        session = sf()
        try:
            repo = HostRepository(session)
            hosts = repo.get_all()
            host_id = hosts[0].id
        finally:
            session.close()

        response = dashboard_client.put(
            f"/dashboard/hosts/{host_id}",
            data={"name": "Updated", "voice": "Puck", "role": "co-host"},
        )
        assert "toast" in response.text
        assert "updated" in response.text.lower()

    def test_update_nonexistent_host_returns_404(self, dashboard_client: TestClient):
        response = dashboard_client.put(
            "/dashboard/hosts/9999",
            data={"name": "Ghost", "voice": "Puck", "role": "host"},
        )
        assert response.status_code == 404


class TestHostDelete:
    """Tests for DELETE /dashboard/hosts/{id}."""

    def test_delete_host_returns_updated_list(self, dashboard_client: TestClient):
        _seed_host(dashboard_client, name="DeleteMe", voice="Kore", role="host")
        sf = dashboard_client.app.state.session_factory
        session = sf()
        try:
            repo = HostRepository(session)
            hosts = repo.get_all()
            host_id = hosts[0].id
        finally:
            session.close()

        response = dashboard_client.delete(f"/dashboard/hosts/{host_id}")
        assert response.status_code == 200
        assert "DeleteMe" not in response.text

    def test_delete_host_returns_toast(self, dashboard_client: TestClient):
        _seed_host(dashboard_client, name="ByeBye", voice="Kore", role="host")
        sf = dashboard_client.app.state.session_factory
        session = sf()
        try:
            repo = HostRepository(session)
            hosts = repo.get_all()
            host_id = hosts[0].id
        finally:
            session.close()

        response = dashboard_client.delete(f"/dashboard/hosts/{host_id}")
        assert "toast" in response.text
        assert "deleted" in response.text.lower()


class TestHostNewForm:
    """Tests for GET /dashboard/hosts/new."""

    def test_new_form_returns_empty_dialog(self, dashboard_client: TestClient):
        response = dashboard_client.get("/dashboard/hosts/new")
        assert response.status_code == 200
        assert "dialog" in response.text.lower()
        # Should have a form with post action
        assert "hx-post" in response.text.lower() or "hx-post" in response.text
