"""Preset CRUD routes for the dashboard."""

from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from sqlalchemy.orm import Session

from src.backend.web.deps import get_db, require_auth, require_csrf
from src.domain.models import Preset
from src.infrastructure.database.repositories import (
    HostRepository,
    PresetRepository,
    StyleRepository,
)

router = APIRouter(
    prefix="/dashboard/presets",
    dependencies=[Depends(require_auth), Depends(require_csrf)],
)


def _render_preset_list(request: Request, db: Session, toast_type: str | None = None, toast_message: str | None = None):
    """Render the full preset list table with resolved host/style names."""
    templates = request.app.state.templates
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

    context = {"request": request, "preset_details": preset_details}

    parts = [templates.TemplateResponse(
        request=request,
        name="partials/presets/row_list.html",
        context=context,
    )]

    if toast_type and toast_message:
        toast_response = templates.TemplateResponse(
            request=request,
            name="partials/toast.html",
            context={"request": request, "toast_type": toast_type, "toast_message": toast_message},
        )
        # Combine HTML responses
        combined_html = parts[0].body.decode() + toast_response.body.decode()
        from fastapi.responses import HTMLResponse
        return HTMLResponse(content=combined_html)

    return parts[0]


@router.get("/new")
def new_preset_form(request: Request, db: Session = Depends(get_db)):
    """Return a form dialog for creating a new preset."""
    templates = request.app.state.templates
    host_repo = HostRepository(db)
    style_repo = StyleRepository(db)

    context = {
        "request": request,
        "hosts": host_repo.get_all(),
        "styles": style_repo.get_all(),
        "preset": None,
        "action": "create",
    }
    return templates.TemplateResponse(
        request=request,
        name="partials/presets/form.html",
        context=context,
    )


@router.post("")
def create_preset(
    request: Request,
    folder_path: str = Form(""),
    host_a_id: int = Form(...),
    host_b_id: int = Form(...),
    style_id: int = Form(...),
    personality_guidance: str = Form(""),
    db: Session = Depends(get_db),
):
    """Create a new preset from form data."""
    if not folder_path.strip():
        templates = request.app.state.templates
        toast_response = templates.TemplateResponse(
            request=request,
            name="partials/toast.html",
            context={
                "request": request,
                "toast_type": "error",
                "toast_message": "Folder path is required",
            },
        )
        from fastapi.responses import HTMLResponse
        return HTMLResponse(content=toast_response.body.decode())

    preset_repo = PresetRepository(db)
    preset_repo.create(
        Preset(
            folder_path=folder_path.strip(),
            host_a_id=host_a_id,
            host_b_id=host_b_id,
            style_id=style_id,
            personality_guidance=personality_guidance.strip() or None,
        )
    )
    return _render_preset_list(request, db, toast_type="success", toast_message="Preset created")


@router.get("/{preset_id}/edit")
def edit_preset_form(request: Request, preset_id: int, db: Session = Depends(get_db)):
    """Return a pre-populated form dialog for editing a preset."""
    templates = request.app.state.templates
    preset_repo = PresetRepository(db)
    host_repo = HostRepository(db)
    style_repo = StyleRepository(db)

    preset = preset_repo.get_by_id(preset_id)
    if preset is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Preset not found")

    context = {
        "request": request,
        "hosts": host_repo.get_all(),
        "styles": style_repo.get_all(),
        "preset": preset,
        "action": "edit",
    }
    return templates.TemplateResponse(
        request=request,
        name="partials/presets/form.html",
        context=context,
    )


@router.put("/{preset_id}")
def update_preset(
    request: Request,
    preset_id: int,
    folder_path: str = Form(...),
    host_a_id: int = Form(...),
    host_b_id: int = Form(...),
    style_id: int = Form(...),
    personality_guidance: str = Form(""),
    db: Session = Depends(get_db),
):
    """Update an existing preset."""
    preset_repo = PresetRepository(db)
    updated = preset_repo.update(
        preset_id,
        folder_path=folder_path.strip(),
        host_a_id=host_a_id,
        host_b_id=host_b_id,
        style_id=style_id,
        personality_guidance=personality_guidance.strip() or None,
    )
    if updated is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Preset not found")

    return _render_preset_list(request, db, toast_type="success", toast_message="Preset updated")


@router.delete("/{preset_id}")
def delete_preset(request: Request, preset_id: int, db: Session = Depends(get_db)):
    """Delete a preset."""
    preset_repo = PresetRepository(db)
    deleted = preset_repo.delete(preset_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Preset not found")

    return _render_preset_list(request, db, toast_type="success", toast_message="Preset deleted")
