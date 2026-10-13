"""Evidence endpoints: upload, link, library, download. Backward-compatible + v2."""

import json
import os
import re

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse, RedirectResponse

import audit_service
import evidence_service
from auth import enforce_account_access, get_current_account, get_current_user
from config import settings
from database import Session, get_db
from models import Account, Evidence, EvidenceLink, User
from schemas import (
    EvidenceLinkedEntity,
    EvidenceLinkRequest,
    EvidenceLinkResponse,
    EvidenceLibraryItem,
    EvidenceLibraryResponse,
    EvidenceResponse,
    EvidenceUpdateRequest,
    EvidenceUploadResponse,
)

router = APIRouter()

ALLOWED_EXTENSIONS = {
    ".pdf", ".doc", ".docx", ".xls", ".xlsx",
    ".png", ".jpg", ".jpeg", ".txt", ".csv",
}


def _sanitize_filename(filename: str) -> str:
    filename = os.path.basename(filename)
    filename = re.sub(r"[^\w\-. ]", "", filename)
    filename = re.sub(r"\.{2,}", ".", filename)
    filename = filename.strip(". ")
    return filename or "unnamed"


def _evidence_to_response(ev: Evidence) -> EvidenceResponse:
    return EvidenceResponse(
        id=ev.id,
        controlId=ev.control_id or "",
        filename=ev.filename,
        fileSize=ev.file_size,
        contentType=ev.content_type,
        uploadedAt=ev.uploaded_at.isoformat() if ev.uploaded_at else "",
        uploadedBy=ev.uploaded_by,
    )


def _evidence_to_upload_response(ev: Evidence, is_duplicate: bool) -> EvidenceUploadResponse:
    tags = []
    if ev.tags:
        try:
            tags = json.loads(ev.tags)
        except (json.JSONDecodeError, TypeError):
            pass
    return EvidenceUploadResponse(
        id=ev.id,
        filename=ev.filename,
        fileSize=ev.file_size,
        contentType=ev.content_type,
        sha256=ev.sha256,
        description=ev.description or "",
        tags=tags,
        uploadedAt=ev.uploaded_at.isoformat() if ev.uploaded_at else "",
        uploadedBy=ev.uploaded_by,
        isDuplicate=is_duplicate,
    )


def _link_to_response(el: EvidenceLink) -> EvidenceLinkResponse:
    return EvidenceLinkResponse(
        id=el.id,
        evidenceId=el.evidence_id,
        entityType=el.entity_type,
        entityId=el.entity_id,
        linkType=el.link_type,
        linkedAt=el.linked_at.isoformat() if el.linked_at else "",
    )


def _validate_upload(file: UploadFile) -> None:
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"File type '{ext}' is not allowed. Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}",
        )


# ---------------------------------------------------------------------------
# V2 Endpoints (org-scoped) — MUST be defined before legacy catch-all routes
# so that literal path segments (upload, library, tags, link, etc.) are matched
# before {control_id} or {evidence_id} path parameters.
# ---------------------------------------------------------------------------


@router.post("/evidence/{account_id}/upload", response_model=EvidenceUploadResponse)
async def upload_evidence_v2(
    account_id: str,
    file: UploadFile = File(...),
    description: str = Form(""),
    tags: str = Form("[]"),  # JSON array string
    account: Account = Depends(get_current_account),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Upload evidence to the org library (not tied to a specific control)."""
    enforce_account_access(account, account_id)
    _validate_upload(file)

    content = await file.read()
    error = evidence_service.validate_file(file.filename or "unnamed", len(content))
    if error:
        raise HTTPException(status_code=400, detail=error)

    safe_name = _sanitize_filename(file.filename or "unnamed")
    try:
        parsed_tags = json.loads(tags) if tags else []
    except json.JSONDecodeError:
        parsed_tags = []

    ev, was_dup = evidence_service.upload(
        db, account_id, user.id, user.name, safe_name,
        content, file.content_type or "application/octet-stream",
        description=description, tags=parsed_tags,
    )

    audit_service.emit(
        db, account_id, "evidence.uploaded",
        actor_user_id=user.id, actor_email=user.email,
        entity_type="evidence", entity_id=ev.id, entity_label=ev.filename,
        after_state={"filename": ev.filename, "sha256": ev.sha256, "was_duplicate": was_dup},
    )
    db.commit()
    return _evidence_to_upload_response(ev, was_dup)


@router.post("/evidence/{account_id}/link", response_model=EvidenceLinkResponse)
def link_evidence(
    account_id: str,
    req: EvidenceLinkRequest,
    account: Account = Depends(get_current_account),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Link an existing evidence file to an entity."""
    enforce_account_access(account, account_id)

    # Verify evidence belongs to this account
    ev = db.get_by_key(Evidence, account_id, id=req.evidence_id)
    if ev and ev.deleted_at is not None:
        ev = None
    if not ev:
        raise HTTPException(status_code=404, detail="Evidence not found")

    el = evidence_service.link(db, req.evidence_id, req.entity_type, req.entity_id, req.link_type, user.id)

    audit_service.emit(
        db, account_id, "evidence.linked",
        actor_user_id=user.id, actor_email=user.email,
        entity_type="evidence", entity_id=ev.id, entity_label=ev.filename,
        after_state={"entity_type": req.entity_type, "entity_id": req.entity_id, "link_type": req.link_type},
    )
    db.commit()
    return _link_to_response(el)


@router.delete("/evidence/{account_id}/links/{link_id}")
def unlink_evidence(
    account_id: str,
    link_id: str,
    account: Account = Depends(get_current_account),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Soft-unlink evidence from an entity."""
    enforce_account_access(account, account_id)

    el = evidence_service.unlink(db, link_id, account_id)
    if not el:
        raise HTTPException(status_code=404, detail="Link not found")

    audit_service.emit(
        db, account_id, "evidence.unlinked",
        actor_user_id=user.id, actor_email=user.email,
        entity_type="evidence_link", entity_id=link_id,
        after_state={"evidence_id": el.evidence_id, "entity_type": el.entity_type, "entity_id": el.entity_id},
    )
    db.commit()
    return {"detail": "Evidence unlinked"}


@router.get("/evidence/{account_id}/library", response_model=EvidenceLibraryResponse)
def search_evidence_library(
    account_id: str,
    q: str = Query("", description="Search filename, description, tags"),
    tag: list[str] = Query([], description="Filter by tags"),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    account: Account = Depends(get_current_account),
    db: Session = Depends(get_db),
):
    """Search the evidence library."""
    enforce_account_access(account, account_id)

    results, total = evidence_service.search_library(
        db, account_id, q=q, tags=tag if tag else None, page=page, per_page=per_page,
    )

    items = []
    for item in results:
        ev = item["evidence"]
        tags_list = []
        if ev.tags:
            try:
                tags_list = json.loads(ev.tags)
            except (json.JSONDecodeError, TypeError):
                pass
        linked_entities = [
            EvidenceLinkedEntity(
                linkId=le["link_id"],
                entityType=le["entity_type"],
                entityId=le["entity_id"],
                entityName=le["entity_name"],
            )
            for le in item.get("linked_entities", [])
        ]
        items.append(EvidenceLibraryItem(
            id=ev.id,
            filename=ev.filename,
            fileSize=ev.file_size,
            contentType=ev.content_type,
            sha256=ev.sha256,
            description=ev.description or "",
            tags=tags_list,
            uploadedAt=ev.uploaded_at.isoformat() if ev.uploaded_at else "",
            uploadedBy=ev.uploaded_by,
            linkCount=item["link_count"],
            linkedEntities=linked_entities,
        ))

    return EvidenceLibraryResponse(items=items, total=total, page=page, perPage=per_page)


@router.get("/evidence/{account_id}/entity/{entity_type}/{entity_id}", response_model=list[EvidenceUploadResponse])
def get_evidence_for_entity(
    account_id: str,
    entity_type: str,
    entity_id: str,
    account: Account = Depends(get_current_account),
    db: Session = Depends(get_db),
):
    """List evidence attached to a specific entity."""
    enforce_account_access(account, account_id)

    items = evidence_service.get_for_entity(db, account_id, entity_type, entity_id)
    return [_evidence_to_upload_response(item["evidence"], False) for item in items]


@router.get("/evidence/{account_id}/tags")
def get_evidence_tags(
    account_id: str,
    account: Account = Depends(get_current_account),
    db: Session = Depends(get_db),
):
    """Get all distinct tags used in the account for autocomplete."""
    enforce_account_access(account, account_id)
    return evidence_service.get_tags(db, account_id)


@router.delete("/evidence/{account_id}/file/{evidence_id}")
def delete_evidence_v2(
    account_id: str,
    evidence_id: str,
    account: Account = Depends(get_current_account),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Soft delete evidence (v2)."""
    enforce_account_access(account, account_id)

    ev = evidence_service.soft_delete(db, evidence_id, account_id)
    if not ev:
        raise HTTPException(status_code=404, detail="Evidence not found")

    audit_service.emit(
        db, account_id, "evidence.deleted",
        actor_user_id=user.id, actor_email=user.email,
        entity_type="evidence", entity_id=evidence_id, entity_label=ev.filename,
    )
    db.commit()
    return {"detail": "Evidence deleted"}


# ---------------------------------------------------------------------------
# Backward-compatible endpoints (legacy control-scoped)
# These use {control_id} path parameters that would catch literal segments
# like "upload", "library", "tags" if placed before the v2 routes above.
# ---------------------------------------------------------------------------


@router.post("/evidence/{account_id}/{control_id}", response_model=EvidenceResponse)
async def upload_evidence_legacy(
    account_id: str,
    control_id: str,
    file: UploadFile = File(...),
    account: Account = Depends(get_current_account),
    db: Session = Depends(get_db),
):
    """Legacy upload: file attached to a specific control."""
    enforce_account_access(account, account_id)
    _validate_upload(file)

    content = await file.read()
    error = evidence_service.validate_file(file.filename or "unnamed", len(content))
    if error:
        raise HTTPException(status_code=400, detail=error)

    safe_name = _sanitize_filename(file.filename or "unnamed")
    ev, _ = evidence_service.upload(
        db, account_id, None, account.name, safe_name,
        content, file.content_type or "application/octet-stream",
    )
    # Set legacy control_id
    ev.control_id = control_id

    # Auto-link to control
    evidence_service.link(db, ev.id, "control", control_id, "primary")

    db.commit()
    return _evidence_to_response(ev)


@router.get("/evidence/{account_id}/{control_id}", response_model=list[EvidenceResponse])
def list_evidence_legacy(
    account_id: str,
    control_id: str,
    account: Account = Depends(get_current_account),
    db: Session = Depends(get_db),
):
    """Legacy: list evidence for a control (via evidence_links)."""
    enforce_account_access(account, account_id)

    items = evidence_service.get_for_entity(db, account_id, "control", control_id)
    return [_evidence_to_response(item["evidence"]) for item in items]


@router.patch("/evidence/{account_id}/{evidence_id}", response_model=EvidenceUploadResponse)
def update_evidence_metadata(
    account_id: str,
    evidence_id: str,
    req: EvidenceUpdateRequest,
    account: Account = Depends(get_current_account),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update evidence description and/or tags."""
    enforce_account_access(account, account_id)

    ev = db.get_by_key(Evidence, account_id, id=evidence_id)
    if ev and ev.deleted_at is not None:
        ev = None
    if not ev:
        raise HTTPException(status_code=404, detail="Evidence not found")

    before = {"description": ev.description, "tags": ev.tags}

    if req.description is not None:
        ev.description = req.description
    if req.tags is not None:
        ev.tags = json.dumps(req.tags)

    audit_service.emit(
        db, account_id, "evidence.updated",
        actor_user_id=user.id, actor_email=user.email,
        entity_type="evidence", entity_id=evidence_id, entity_label=ev.filename,
        before_state=before,
        after_state={"description": ev.description, "tags": ev.tags},
    )
    db.commit()
    return _evidence_to_upload_response(ev, False)


@router.get("/evidence/{account_id}/{control_id}/{evidence_id}/download")
def download_evidence_legacy(
    account_id: str,
    control_id: str,
    evidence_id: str,
    account: Account = Depends(get_current_account),
    db: Session = Depends(get_db),
):
    """Legacy download by control_id."""
    enforce_account_access(account, account_id)

    result = evidence_service.get_download_url(db, evidence_id, account_id)
    if not result:
        raise HTTPException(status_code=404, detail="Evidence not found")

    url_or_path, filename, is_signed = result
    if is_signed:
        return RedirectResponse(url=url_or_path)
    return FileResponse(path=url_or_path, filename=filename)


@router.delete("/evidence/{account_id}/{control_id}/{evidence_id}")
def delete_evidence_legacy(
    account_id: str,
    control_id: str,
    evidence_id: str,
    account: Account = Depends(get_current_account),
    db: Session = Depends(get_db),
):
    """Legacy delete."""
    enforce_account_access(account, account_id)

    ev = evidence_service.soft_delete(db, evidence_id, account_id)
    if not ev:
        raise HTTPException(status_code=404, detail="Evidence not found")

    audit_service.emit(
        db, account_id, "evidence.deleted",
        entity_type="evidence", entity_id=evidence_id, entity_label=ev.filename,
    )
    db.commit()
    return {"detail": "Evidence deleted"}


@router.get("/evidence/{account_id}/{evidence_id}/download-url")
def get_evidence_download_url(
    account_id: str,
    evidence_id: str,
    account: Account = Depends(get_current_account),
    db: Session = Depends(get_db),
):
    """Get a download URL (signed for S3, direct for filesystem)."""
    enforce_account_access(account, account_id)

    result = evidence_service.get_download_url(db, evidence_id, account_id)
    if not result:
        raise HTTPException(status_code=404, detail="Evidence not found")

    url_or_path, filename, is_signed = result
    if is_signed:
        audit_service.emit(
            db, account_id, "evidence.downloaded",
            entity_type="evidence", entity_id=evidence_id,
        )
        db.commit()
        return {"url": url_or_path, "filename": filename}
    else:
        return FileResponse(path=url_or_path, filename=filename)
