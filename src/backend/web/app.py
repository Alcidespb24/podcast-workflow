"""FastAPI application factory for the podcast web server."""

from __future__ import annotations

import os
from collections.abc import Callable
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING, AsyncIterator

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from src.backend.web.routes.rss import router as rss_router
from src.config import Settings
from src.domain.models import Episode

if TYPE_CHECKING:
    from src.backend.watcher.service import WatcherService


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Start watcher on app startup, stop on shutdown."""
    watcher: WatcherService | None = getattr(app.state, "watcher_service", None)
    if watcher is not None and app.state.settings.watcher_enabled:
        watcher.start()
    yield
    if watcher is not None:
        watcher.stop()


def create_app(
    settings: Settings,
    get_episodes: Callable[[], list[Episode]] | None = None,
    watcher_service: "WatcherService | None" = None,
) -> FastAPI:
    """Create and configure the FastAPI application.

    Args:
        settings: Application settings with base_url, episodes_dir, etc.
        get_episodes: Optional callable returning list[Episode] for RSS feed.
            Defaults to returning an empty list (useful for testing static serving).
        watcher_service: Optional WatcherService for folder-watch automation.

    Returns:
        Configured FastAPI application instance.
    """
    app = FastAPI(title="Podcast Workflow", lifespan=lifespan)

    # Store settings and episode getter on app state for route access
    app.state.settings = settings
    app.state.get_episodes = get_episodes or (lambda: [])
    app.state.watcher_service = watcher_service

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
