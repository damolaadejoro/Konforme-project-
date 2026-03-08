import os
import re
import uuid

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from auth import get_current_account, enforce_account_access
from config import settings
from database import get_db
from models import Account, Evidence
from schemas import EvidenceResponse

router = APIRouter()

ALLOWED_CONTENT_TYPES = {
    "application/pdf",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.ms-excel",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "image/png",
    "image/jpeg",
    "text/plain",
    "text/csv",
}

ALLOWED_EXTENSIONS = {
    ".pdf", ".doc", ".docx", ".xls", ".xlsx",
    ".png", ".jpg", ".jpeg", ".txt", ".csv",
}


def _sanitize_filename(filename: str) -> str:
    """Remove path separators and dangerous characters from filename."""
    # Strip any directory components
    filename = os.path.basename(filename)
    # Remove anything that isn't alphanumeric, dash, underscore, dot, or space
    filename = re.sub(r"[^\w\-. ]", "", filename)
    # Collapse multiple dots/spaces
    filename = re.sub(r"\.{2,}", ".", filename)
    filename = filename.strip(". ")
    return filename or "unnamed"


def _get_upload_path(account_id: str, control_id: str) -> str:
    """Build the directory path for storing evidence files."""
    # Prevent path traversal by validating components
    if ".." in account_id or "/" in account_id or "\\" in account_id:
        raise HTTPException(status_code=400, detail="Invalid account ID")
    if ".." in control_id or "/" in control_id or "\\" in control_id:
        raise HTTPException(status_code=400, detail="Invalid control ID")
    return os.path.join(settings.upload_dir, account_id, control_id)


def _evidence_to_response(ev: Evidence) -> EvidenceResponse:
    return EvidenceResponse(
        id=ev.id,
        controlId=ev.control_id,
        filename=ev.filename,
        fileSize=ev.file_size,
        contentType=ev.content_type,
        uploadedAt=ev.uploaded_at.isoformat(),
        uploadedBy=ev.uploaded_by,
    )


@router.post("/evidence/{account_id}/{control_id}", response_model=EvidenceResponse)
async def upload_evidence(
    account_id: str,
    control_id: str,
    file: UploadFile = File(...),
    account: Account = Depends(get_current_account),
    db: Session = Depends(get_db),
):
    enforce_account_access(account, account_id)

    # Validate file extension
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"File type '{ext}' is not allowed. Allowed types: {', '.join(sorted(ALLOWED_EXTENSIONS))}",
        )

    # Validate content type
    if file.content_type and file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Content type '{file.content_type}' is not allowed",
        )

    # Read file and check size
    max_bytes = settings.max_upload_size_mb * 1024 * 1024
    content = await file.read()
    if len(content) > max_bytes:
        raise HTTPException(
            status_code=400,
            detail=f"File size exceeds the {settings.max_upload_size_mb}MB limit",
        )

    # Prepare storage
    safe_filename = _sanitize_filename(file.filename)
    stored_filename = f"{uuid.uuid4()}_{safe_filename}"
    upload_dir = _get_upload_path(account_id, control_id)
    os.makedirs(upload_dir, exist_ok=True)

    file_path = os.path.join(upload_dir, stored_filename)

    # Write file to disk
    with open(file_path, "wb") as f:
        f.write(content)

    # Create DB record
    evidence = Evidence(
        account_id=account_id,
        control_id=control_id,
        filename=safe_filename,
        stored_filename=stored_filename,
        file_size=len(content),
        content_type=file.content_type or "application/octet-stream",
        uploaded_by=account.name,
    )
    db.add(evidence)
    db.commit()
    db.refresh(evidence)

    return _evidence_to_response(evidence)


@router.get("/evidence/{account_id}/{control_id}", response_model=list[EvidenceResponse])
def list_evidence(
    account_id: str,
    control_id: str,
    account: Account = Depends(get_current_account),
    db: Session = Depends(get_db),
):
    enforce_account_access(account, account_id)

    evidence_list = (
        db.query(Evidence)
        .filter(Evidence.account_id == account_id, Evidence.control_id == control_id)
        .order_by(Evidence.uploaded_at.desc())
        .all()
    )

    return [_evidence_to_response(ev) for ev in evidence_list]


@router.get("/evidence/{account_id}/{control_id}/{evidence_id}/download")
def download_evidence(
    account_id: str,
    control_id: str,
    evidence_id: str,
    account: Account = Depends(get_current_account),
    db: Session = Depends(get_db),
):
    enforce_account_access(account, account_id)

    evidence = (
        db.query(Evidence)
        .filter(
            Evidence.id == evidence_id,
            Evidence.account_id == account_id,
            Evidence.control_id == control_id,
        )
        .first()
    )
    if not evidence:
        raise HTTPException(status_code=404, detail="Evidence not found")

    upload_dir = _get_upload_path(account_id, control_id)
    file_path = os.path.join(upload_dir, evidence.stored_filename)

    if not os.path.isfile(file_path):
        raise HTTPException(status_code=404, detail="Evidence file not found on disk")

    return FileResponse(
        path=file_path,
        filename=evidence.filename,
        media_type=evidence.content_type,
    )


@router.delete("/evidence/{account_id}/{control_id}/{evidence_id}")
def delete_evidence(
    account_id: str,
    control_id: str,
    evidence_id: str,
    account: Account = Depends(get_current_account),
    db: Session = Depends(get_db),
):
    enforce_account_access(account, account_id)

    evidence = (
        db.query(Evidence)
        .filter(
            Evidence.id == evidence_id,
            Evidence.account_id == account_id,
            Evidence.control_id == control_id,
        )
        .first()
    )
    if not evidence:
        raise HTTPException(status_code=404, detail="Evidence not found")

    # Delete file from disk
    upload_dir = _get_upload_path(account_id, control_id)
    file_path = os.path.join(upload_dir, evidence.stored_filename)
    if os.path.isfile(file_path):
        os.remove(file_path)

    # Delete DB record
    db.delete(evidence)
    db.commit()

    return {"detail": "Evidence deleted"}
