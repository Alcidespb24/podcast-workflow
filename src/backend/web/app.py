"""FastAPI application factory for the podcast web server."""

import os

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from src.backend.web.routes.rss import router as rss_router
from src.config import Settings
from src.domain.models import Episode


def create_app(
    settings: Settings,
    get_episodes: callable = None,
) -> FastAPI:
    """Create and configure the FastAPI application.

    Args:
        settings: Application settings with base_url, episodes_dir, etc.
        get_episodes: Optional callable returning list[Episode] for RSS feed.
            Defaults to returning an empty list (useful for testing static serving).

    Returns:
        Configured FastAPI application instance.
    """
    app = FastAPI(title="Podcast Workflow")

    # Store settings and episode getter on app state for route access
    app.state.settings = settings
    app.state.get_episodes = get_episodes or (lambda: [])

    # Ensure episodes directory exists
    os.makedirs(settings.episodes_dir, exist_ok=True)

    # Mount static file serving for MP3 episodes
    app.mount(
        "/episodes",
        StaticFiles(directory=settings.episodes_dir),
        name="episodes",
    )

    # Include RSS feed route
    app.include_router(rss_router)

    return app
