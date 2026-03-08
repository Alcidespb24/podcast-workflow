"""RSS feed endpoint for serving the podcast feed."""

from fastapi import APIRouter, Request
from fastapi.responses import Response

from src.infrastructure.rss import build_podcast_feed

router = APIRouter()


@router.get("/feed.xml")
def get_feed(request: Request) -> Response:
    """Generate and return the podcast RSS feed.

    Builds the feed on-the-fly from the episode repository.
    Returns XML with content-type application/rss+xml.
    """
    settings = request.app.state.settings
    episodes = request.app.state.get_episodes()

    xml = build_podcast_feed(
        podcast_title=settings.podcast_name,
        podcast_description=f"{settings.podcast_name} - auto-generated podcast feed",
        base_url=settings.base_url,
        episodes=episodes,
    )
    return Response(content=xml, media_type="application/rss+xml")
