"""Dashboard routes for the podcast web interface."""

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse

from src.backend.web.deps import require_auth
from src.domain.models import JobState
from src.infrastructure.database.repositories import (
    EpisodeRepository,
    JobRepository,
)

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


def _render_page(request: Request, page: str) -> HTMLResponse:
    """Render a full page or HTMX partial depending on request type."""
    templates = request.app.state.templates
    partial = _PAGES[page]
    context = {"request": request, "active_page": page}

    # Add default sidebar status context for full-page renders
    context.setdefault("watcher_running", False)
    context.setdefault("pending_count", 0)
    context.setdefault("last_episode_time", None)

    if request.headers.get("HX-Request"):
        return templates.TemplateResponse(request=request, name=partial, context=context)

    context["content_template"] = partial
    return templates.TemplateResponse(request=request, name="base.html", context=context)


@router.get("/episodes")
def episodes_page(request: Request):
    """Render the episodes page."""
    return _render_page(request, "episodes")


@router.get("/hosts")
def hosts_page(request: Request):
    """Render the hosts page."""
    return _render_page(request, "hosts")


@router.get("/styles")
def styles_page(request: Request):
    """Render the styles page."""
    return _render_page(request, "styles")


@router.get("/presets")
def presets_page(request: Request):
    """Render the presets page."""
    return _render_page(request, "presets")


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
