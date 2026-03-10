"""Host CRUD API routes for the dashboard."""

from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from src.backend.web.deps import get_db, require_auth, require_csrf
from src.domain.models import Host
from src.infrastructure.database.repositories import HostRepository

router = APIRouter(
    prefix="/dashboard/hosts",
    dependencies=[Depends(require_auth), Depends(require_csrf)],
)


def _render_host_list(request: Request, db: Session) -> str:
    """Render the host list partial HTML."""
    templates = request.app.state.templates
    repo = HostRepository(db)
    hosts = repo.get_all()
    return templates.TemplateResponse(
        request=request,
        name="partials/hosts/list.html",
        context={"request": request, "hosts": hosts, "active_page": "hosts"},
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
def new_host_form(request: Request):
    """Return an empty host form dialog for creating a new host."""
    templates = request.app.state.templates
    return templates.TemplateResponse(
        request=request,
        name="partials/hosts/form.html",
        context={"request": request, "host": None, "action": "create", "errors": None},
    )


@router.post("", response_class=HTMLResponse)
def create_host(
    request: Request,
    db: Session = Depends(get_db),
    name: str = Form(""),
    voice: str = Form(""),
    role: str = Form("host"),
):
    """Create a new host and return the updated list with toast."""
    # Validate
    if not name.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Name is required",
        )
    if not voice.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Voice is required",
        )

    repo = HostRepository(db)
    host = repo.create(Host(name=name.strip(), voice=voice.strip(), role=role))

    list_html = _render_host_list(request, db)
    toast_html = _render_toast(request, "success", f"Host '{host.name}' created")
    return HTMLResponse(content=list_html + toast_html)


@router.get("/{host_id}/edit", response_class=HTMLResponse)
def edit_host_form(
    host_id: int,
    request: Request,
    db: Session = Depends(get_db),
):
    """Return a pre-populated host form dialog for editing."""
    repo = HostRepository(db)
    host = repo.get_by_id(host_id)
    if host is None:
        raise HTTPException(status_code=404, detail="Host not found")

    templates = request.app.state.templates
    return templates.TemplateResponse(
        request=request,
        name="partials/hosts/form.html",
        context={"request": request, "host": host, "action": "edit", "errors": None},
    )


@router.put("/{host_id}", response_class=HTMLResponse)
def update_host(
    host_id: int,
    request: Request,
    db: Session = Depends(get_db),
    name: str = Form(""),
    voice: str = Form(""),
    role: str = Form("host"),
):
    """Update an existing host and return the updated list with toast."""
    if not name.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Name is required",
        )

    repo = HostRepository(db)
    host = repo.update(host_id, name=name.strip(), voice=voice.strip(), role=role)
    if host is None:
        raise HTTPException(status_code=404, detail="Host not found")

    list_html = _render_host_list(request, db)
    toast_html = _render_toast(request, "success", f"Host '{host.name}' updated")
    return HTMLResponse(content=list_html + toast_html)


@router.delete("/{host_id}", response_class=HTMLResponse)
def delete_host(
    host_id: int,
    request: Request,
    db: Session = Depends(get_db),
):
    """Delete a host and return the updated list with toast."""
    repo = HostRepository(db)
    # Get host name before deleting for the toast message
    host = repo.get_by_id(host_id)
    host_name = host.name if host else "Host"

    deleted = repo.delete(host_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Host not found")

    list_html = _render_host_list(request, db)
    toast_html = _render_toast(request, "success", f"Host '{host_name}' deleted")
    return HTMLResponse(content=list_html + toast_html)
