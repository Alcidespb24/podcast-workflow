"""Integration tests for Style CRUD dashboard routes."""

import base64

import pytest
from fastapi.testclient import TestClient

from src.domain.models import Style
from src.infrastructure.database.repositories import StyleRepository


AUTH_HEADER = f"Basic {base64.b64encode(b'admin:testpass').decode('ascii')}"


def _seed_style(
    dashboard_client: TestClient,
    name: str = "Casual",
    tone: str = "Relaxed and friendly",
    personality_guidance: str | None = None,
) -> None:
    """Create a style via the session_factory for test seeding."""
    sf = dashboard_client.app.state.session_factory
    session = sf()
    try:
        repo = StyleRepository(session)
        repo.create(Style(name=name, tone=tone, personality_guidance=personality_guidance))
        session.commit()
    finally:
        session.close()


class TestStyleList:
    """Tests for GET /dashboard/styles."""

    def test_returns_200_with_auth(self, dashboard_client: TestClient):
        response = dashboard_client.get("/dashboard/styles")
        assert response.status_code == 200

    def test_contains_styles_heading(self, dashboard_client: TestClient):
        response = dashboard_client.get("/dashboard/styles")
        assert "Styles" in response.text

    def test_htmx_request_returns_partial(self, dashboard_client: TestClient):
        response = dashboard_client.get(
            "/dashboard/styles",
            headers={"HX-Request": "true"},
        )
        assert response.status_code == 200
        assert "<!DOCTYPE html>" not in response.text
        assert "Styles" in response.text

    def test_full_request_returns_page_with_sidebar(self, dashboard_client: TestClient):
        response = dashboard_client.get("/dashboard/styles")
        assert response.status_code == 200
        assert "<!DOCTYPE html>" in response.text
        assert "sidebar" in response.text

    def test_lists_seeded_styles(self, dashboard_client: TestClient):
        _seed_style(dashboard_client, name="Casual", tone="Relaxed")
        _seed_style(dashboard_client, name="Formal", tone="Professional")
        response = dashboard_client.get(
            "/dashboard/styles",
            headers={"HX-Request": "true"},
        )
        assert "Casual" in response.text
        assert "Formal" in response.text

    def test_returns_401_without_auth(self, dashboard_client: TestClient):
        client = TestClient(dashboard_client.app)
        response = client.get("/dashboard/styles")
        assert response.status_code == 401


class TestStyleCreate:
    """Tests for POST /dashboard/styles."""

    def test_create_style_returns_updated_list(self, dashboard_client: TestClient):
        response = dashboard_client.post(
            "/dashboard/styles",
            data={"name": "NewStyle", "tone": "Energetic", "personality_guidance": ""},
        )
        assert response.status_code == 200
        assert "NewStyle" in response.text

    def test_create_style_returns_toast(self, dashboard_client: TestClient):
        response = dashboard_client.post(
            "/dashboard/styles",
            data={"name": "ToastStyle", "tone": "Calm", "personality_guidance": ""},
        )
        assert "toast" in response.text
        assert "created" in response.text.lower()

    def test_create_style_missing_name_returns_422(self, dashboard_client: TestClient):
        response = dashboard_client.post(
            "/dashboard/styles",
            data={"name": "", "tone": "Any", "personality_guidance": ""},
        )
        assert response.status_code == 422

    def test_create_style_with_optional_personality_guidance(self, dashboard_client: TestClient):
        response = dashboard_client.post(
            "/dashboard/styles",
            data={
                "name": "Guided",
                "tone": "Thoughtful",
                "personality_guidance": "Be curious and ask probing questions",
            },
        )
        assert response.status_code == 200
        assert "Guided" in response.text

    def test_create_style_requires_auth(self, dashboard_client: TestClient):
        client = TestClient(dashboard_client.app)
        response = client.post(
            "/dashboard/styles",
            data={"name": "NoAuth", "tone": "Any", "personality_guidance": ""},
        )
        assert response.status_code == 401


class TestStyleEdit:
    """Tests for GET /dashboard/styles/{id}/edit."""

    def test_edit_form_loads_with_style_data(self, dashboard_client: TestClient):
        _seed_style(dashboard_client, name="EditMe", tone="Original")
        sf = dashboard_client.app.state.session_factory
        session = sf()
        try:
            repo = StyleRepository(session)
            styles = repo.get_all()
            style_id = styles[0].id
        finally:
            session.close()

        response = dashboard_client.get(f"/dashboard/styles/{style_id}/edit")
        assert response.status_code == 200
        assert "EditMe" in response.text
        assert "dialog" in response.text.lower()


class TestStyleUpdate:
    """Tests for PUT /dashboard/styles/{id}."""

    def test_update_style_returns_updated_list(self, dashboard_client: TestClient):
        _seed_style(dashboard_client, name="OldStyle", tone="Old tone")
        sf = dashboard_client.app.state.session_factory
        session = sf()
        try:
            repo = StyleRepository(session)
            styles = repo.get_all()
            style_id = styles[0].id
        finally:
            session.close()

        response = dashboard_client.put(
            f"/dashboard/styles/{style_id}",
            data={"name": "UpdatedStyle", "tone": "New tone", "personality_guidance": ""},
        )
        assert response.status_code == 200
        assert "UpdatedStyle" in response.text

    def test_update_style_returns_toast(self, dashboard_client: TestClient):
        _seed_style(dashboard_client, name="ToastUpdate", tone="Some tone")
        sf = dashboard_client.app.state.session_factory
        session = sf()
        try:
            repo = StyleRepository(session)
            styles = repo.get_all()
            style_id = styles[0].id
        finally:
            session.close()

        response = dashboard_client.put(
            f"/dashboard/styles/{style_id}",
            data={"name": "Updated", "tone": "New", "personality_guidance": ""},
        )
        assert "toast" in response.text
        assert "updated" in response.text.lower()

    def test_update_nonexistent_style_returns_404(self, dashboard_client: TestClient):
        response = dashboard_client.put(
            "/dashboard/styles/9999",
            data={"name": "Ghost", "tone": "None", "personality_guidance": ""},
        )
        assert response.status_code == 404


class TestStyleDelete:
    """Tests for DELETE /dashboard/styles/{id}."""

    def test_delete_style_returns_updated_list(self, dashboard_client: TestClient):
        _seed_style(dashboard_client, name="DeleteMe", tone="Temp")
        sf = dashboard_client.app.state.session_factory
        session = sf()
        try:
            repo = StyleRepository(session)
            styles = repo.get_all()
            style_id = styles[0].id
        finally:
            session.close()

        response = dashboard_client.delete(f"/dashboard/styles/{style_id}")
        assert response.status_code == 200
        # Style removed from the list table (name still appears in toast)
        assert "No styles configured yet" in response.text or "<tbody>" not in response.text

    def test_delete_style_returns_toast(self, dashboard_client: TestClient):
        _seed_style(dashboard_client, name="ByeBye", tone="Temp")
        sf = dashboard_client.app.state.session_factory
        session = sf()
        try:
            repo = StyleRepository(session)
            styles = repo.get_all()
            style_id = styles[0].id
        finally:
            session.close()

        response = dashboard_client.delete(f"/dashboard/styles/{style_id}")
        assert "toast" in response.text
        assert "deleted" in response.text.lower()


class TestStyleNewForm:
    """Tests for GET /dashboard/styles/new."""

    def test_new_form_returns_empty_dialog(self, dashboard_client: TestClient):
        response = dashboard_client.get("/dashboard/styles/new")
        assert response.status_code == 200
        assert "dialog" in response.text.lower()
        assert "hx-post" in response.text.lower() or "hx-post" in response.text
