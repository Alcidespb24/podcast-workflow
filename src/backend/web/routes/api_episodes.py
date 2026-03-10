"""Episode API routes for the dashboard."""

import os

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from src.backend.web.deps import get_db, require_auth, require_csrf
from src.infrastructure.database.repositories import EpisodeRepository
from src.infrastructure.rss import build_podcast_feed

router = APIRouter(
    prefix="/dashboard/episodes",
    dependencies=[Depends(require_auth), Depends(require_csrf)],
)


@router.delete("/{episode_id}", response_class=HTMLResponse)
def delete_episode(
    episode_id: int,
    request: Request,
    db: Session = Depends(get_db),
):
    """Delete an episode, its MP3 file, and regenerate the RSS feed."""
    settings = request.app.state.settings
    repo = EpisodeRepository(db)

    episode = repo.get_by_id(episode_id)
    if episode is None:
        raise HTTPException(status_code=404, detail="Episode not found")

    title = episode.title

    # Delete MP3 file
    mp3_path = os.path.join(settings.episodes_dir, episode.filename)
    if os.path.exists(mp3_path):
        os.remove(mp3_path)

    # Delete from database
    repo.delete(episode_id)
    db.commit()

    # Regenerate RSS feed
    all_episodes = repo.get_all()
    feed_xml = build_podcast_feed(
        settings.podcast_name,
        settings.podcast_description or settings.podcast_name,
        settings.base_url,
        all_episodes,
        email=settings.podcast_email,
        cover_url=settings.podcast_cover_url,
    )
    feed_path = os.path.join(settings.episodes_dir, "feed.xml")
    with open(feed_path, "w", encoding="utf-8") as f:
        f.write(feed_xml)

    # Return updated episode list + toast
    templates = request.app.state.templates
    from src.backend.web.routes.dashboard import episodes_page
    # Re-fetch items for the list
    items = []
    for ep in repo.get_all():
        items.append({
            "type": "episode",
            "title": ep.title,
            "date": ep.published_at,
            "status": "complete",
            "episode": ep,
        })

    list_html = templates.TemplateResponse(
        request=request,
        name="partials/episodes/cards.html",
        context={"request": request, "items": items, "active_filter": None},
    ).body.decode("utf-8")

    toast_html = templates.TemplateResponse(
        request=request,
        name="partials/toast.html",
        context={"request": request, "toast_type": "success", "toast_message": f"'{title}' deleted — will be removed from Spotify on next feed poll"},
    ).body.decode("utf-8")

    return HTMLResponse(content=list_html + toast_html)
