"""Style CRUD API routes for the dashboard."""

from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from src.backend.web.deps import get_db, require_auth
from src.domain.models import Style
from src.infrastructure.database.repositories import StyleRepository

router = APIRouter(
    prefix="/dashboard/styles",
    dependencies=[Depends(require_auth)],
)


def _render_style_list(request: Request, db: Session) -> str:
    """Render the style list partial HTML."""
    templates = request.app.state.templates
    repo = StyleRepository(db)
    styles = repo.get_all()
    return templates.TemplateResponse(
        request=request,
        name="partials/styles/list.html",
        context={"request": request, "styles": styles, "active_page": "styles"},
    ).body.decode("utf-8")


def _render_toast(request: Request, toast_type: str, toast_message: str) -> str:
    """Render the toast partial HTML."""
    templates = request.app.state.templates
    return templates.TemplateResponse(
        request=request,
        name="partials/toast.html",
        context={
            "request": request,
            "toast_type": toast_type,
            "toast_message": toast_message,
        },
    ).body.decode("utf-8")


@router.get("/new", response_class=HTMLResponse)
def new_style_form(request: Request):
    """Return an empty style form dialog for creating a new style."""
    templates = request.app.state.templates
    return templates.TemplateResponse(
        request=request,
        name="partials/styles/form.html",
        context={"request": request, "style": None, "action": "create", "errors": None},
    )


@router.post("", response_class=HTMLResponse)
def create_style(
    request: Request,
    db: Session = Depends(get_db),
    name: str = Form(""),
    tone: str = Form(""),
    personality_guidance: str = Form(""),
):
    """Create a new style and return the updated list with toast."""
    if not name.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Name is required",
        )
    if not tone.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Tone is required",
        )

    pg = personality_guidance.strip() or None
    repo = StyleRepository(db)
    style = repo.create(Style(name=name.strip(), tone=tone.strip(), personality_guidance=pg))

    list_html = _render_style_list(request, db)
    toast_html = _render_toast(request, "success", f"Style '{style.name}' created")
    return HTMLResponse(content=list_html + toast_html)


@router.get("/{style_id}/edit", response_class=HTMLResponse)
def edit_style_form(
    style_id: int,
    request: Request,
    db: Session = Depends(get_db),
):
    """Return a pre-populated style form dialog for editing."""
    repo = StyleRepository(db)
    style = repo.get_by_id(style_id)
    if style is None:
        raise HTTPException(status_code=404, detail="Style not found")

    templates = request.app.state.templates
    return templates.TemplateResponse(
        request=request,
        name="partials/styles/form.html",
        context={"request": request, "style": style, "action": "edit", "errors": None},
    )


@router.put("/{style_id}", response_class=HTMLResponse)
def update_style(
    style_id: int,
    request: Request,
    db: Session = Depends(get_db),
    name: str = Form(""),
    tone: str = Form(""),
    personality_guidance: str = Form(""),
):
    """Update an existing style and return the updated list with toast."""
    if not name.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Name is required",
        )

    pg = personality_guidance.strip() or None
    repo = StyleRepository(db)
    style = repo.update(
        style_id,
        name=name.strip(),
        tone=tone.strip(),
        personality_guidance=pg,
    )
    if style is None:
        raise HTTPException(status_code=404, detail="Style not found")

    list_html = _render_style_list(request, db)
    toast_html = _render_toast(request, "success", f"Style '{style.name}' updated")
    return HTMLResponse(content=list_html + toast_html)


@router.delete("/{style_id}", response_class=HTMLResponse)
def delete_style(
    style_id: int,
    request: Request,
    db: Session = Depends(get_db),
):
    """Delete a style and return the updated list with toast."""
    repo = StyleRepository(db)
    style = repo.get_by_id(style_id)
    style_name = style.name if style else "Style"

    deleted = repo.delete(style_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Style not found")

    list_html = _render_style_list(request, db)
    toast_html = _render_toast(request, "success", f"Style '{style_name}' deleted")
    return HTMLResponse(content=list_html + toast_html)
