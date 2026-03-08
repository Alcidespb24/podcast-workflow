"""Dashboard routes for the podcast web interface."""

from fastapi import APIRouter, Depends, Request

from src.backend.web.deps import require_auth

router = APIRouter(
    prefix="/dashboard",
    dependencies=[Depends(require_auth)],
)


@router.get("/episodes")
def episodes_page(request: Request):
    """Render the episodes page."""
    templates = request.app.state.templates
    return templates.TemplateResponse(
        request=request,
        name="base.html",
        context={
            "request": request,
            "active_page": "episodes",
            "content_template": "partials/episodes/list.html",
        },
    )
