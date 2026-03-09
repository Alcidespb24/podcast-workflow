"""Dashboard routes for the podcast web interface."""

import os
from typing import Any

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from src.backend.web.deps import get_db, require_auth
from src.domain.models import JobState
from src.infrastructure.database.repositories import (
    EpisodeRepository,
    HostRepository,
    JobRepository,
    PresetRepository,
    StyleRepository,
)

# In-progress job states for filtering
_IN_PROGRESS_STATES = {JobState.PENDING, JobState.PROCESSING, JobState.ENCODING, JobState.PUBLISHING}

router = APIRouter(
    prefix="/dashboard",
    dependencies=[Depends(require_auth)],
)

# -- Page configuration for DRY endpoint creation --

_PAGES = {
    "episodes": "partials/episodes/list.html",
    "hosts": "partials/hosts/list.html",
    "styles": "partials/styles/list.html",
    "presets": "partials/presets/list.html",
}


def _render_page(request: Request, page: str, extra: dict | None = None) -> HTMLResponse:
    """Render a full page or HTMX partial depending on request type."""
    templates = request.app.state.templates
    partial = _PAGES[page]
    context: dict = {"request": request, "active_page": page}
    if extra:
        context.update(extra)

    # Add default sidebar status context for full-page renders
    context.setdefault("watcher_running", False)
    context.setdefault("pending_count", 0)
    context.setdefault("last_episode_time", None)

    if request.headers.get("HX-Request"):
        return templates.TemplateResponse(request=request, name=partial, context=context)

    context["content_template"] = partial
    return templates.TemplateResponse(request=request, name="base.html", context=context)


@router.get("/episodes")
def episodes_page(
    request: Request,
    status: str | None = None,
    db: Session = Depends(get_db),
):
    """Render the episodes page with combined episode and job history.

    Args:
        status: Optional filter -- "complete", "failed", "in_progress", or None for all.
    """
    episode_repo = EpisodeRepository(db)
    job_repo = JobRepository(db)

    items: list[dict[str, Any]] = []

    # Add completed episodes (unless filtering to non-complete statuses)
    if status is None or status == "complete":
        for ep in episode_repo.get_all():
            items.append({
                "type": "episode",
                "title": ep.title,
                "date": ep.published_at,
                "status": "complete",
                "episode": ep,
            })

    # Add non-complete jobs (unless filtering to complete only)
    if status != "complete":
        non_complete_states = [
            JobState.PENDING, JobState.PROCESSING, JobState.ENCODING,
            JobState.PUBLISHING, JobState.FAILED,
        ]
        for job in job_repo.get_all(states=non_complete_states):
            job_status = job.state.value
            # Apply status filter
            if status == "failed" and job_status != "failed":
                continue
            if status == "in_progress" and job.state not in _IN_PROGRESS_STATES:
                continue
            items.append({
                "type": "job",
                "title": os.path.basename(job.source_file),
                "date": job.created_at,
                "status": job_status,
                "job": job,
            })

    # Sort by date descending (newest first)
    items.sort(key=lambda x: x["date"] or 0, reverse=True)

    # Filter request targets #episode-list — return cards only
    if request.headers.get("HX-Target") == "episode-list":
        templates = request.app.state.templates
        context = {"request": request, "items": items, "active_filter": status}
        return templates.TemplateResponse(
            request=request,
            name="partials/episodes/cards.html",
            context=context,
        )

    return _render_page(
        request,
        "episodes",
        extra={"items": items, "active_filter": status},
    )


@router.get("/hosts")
def hosts_page(request: Request, db: Session = Depends(get_db)):
    """Render the hosts page with all hosts from the database."""
    repo = HostRepository(db)
    hosts = repo.get_all()
    return _render_page(request, "hosts", extra={"hosts": hosts})


@router.get("/styles")
def styles_page(request: Request, db: Session = Depends(get_db)):
    """Render the styles page with all styles from the database."""
    repo = StyleRepository(db)
    styles = repo.get_all()
    return _render_page(request, "styles", extra={"styles": styles})


@router.get("/presets")
def presets_page(request: Request, db: Session = Depends(get_db)):
    """Render the presets page with resolved host/style names."""
    preset_repo = PresetRepository(db)
    host_repo = HostRepository(db)
    style_repo = StyleRepository(db)

    presets = preset_repo.get_all()
    preset_details = []
    for preset in presets:
        host_a = host_repo.get_by_id(preset.host_a_id)
        host_b = host_repo.get_by_id(preset.host_b_id)
        style = style_repo.get_by_id(preset.style_id)
        preset_details.append({
            "preset": preset,
            "host_a_name": host_a.name if host_a else "Unknown",
            "host_b_name": host_b.name if host_b else "Unknown",
            "style_name": style.name if style else "Unknown",
        })

    return _render_page(request, "presets", extra={"preset_details": preset_details})


# Status endpoint -- no auth required (HTMX polling from authenticated page)
status_router = APIRouter(prefix="/dashboard")


@status_router.get("/status")
def sidebar_status(request: Request):
    """Return sidebar status partial with watcher state and pending job count."""
    templates = request.app.state.templates

    # Check watcher status
    watcher = getattr(request.app.state, "watcher_service", None)
    watcher_running = False
    if watcher is not None:
        watcher_running = getattr(watcher, "is_running", False)

    # Query pending jobs and latest episode via session (if available)
    pending_count = 0
    last_episode_time = None
    session_factory = getattr(request.app.state, "session_factory", None)
    if session_factory is not None:
        session = session_factory()
        try:
            job_repo = JobRepository(session)
            pending_jobs = job_repo.get_all(states=[JobState.PENDING])
            pending_count = len(pending_jobs)

            episode_repo = EpisodeRepository(session)
            episodes = episode_repo.get_all()
            if episodes:
                last_episode_time = episodes[0].published_at.strftime("%Y-%m-%d %H:%M")
        finally:
            session.close()

    context = {
        "request": request,
        "watcher_running": watcher_running,
        "pending_count": pending_count,
        "last_episode_time": last_episode_time,
    }
    return templates.TemplateResponse(
        request=request,
        name="partials/sidebar_status.html",
        context=context,
    )
