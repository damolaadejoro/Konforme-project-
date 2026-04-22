"""Evidence business logic: upload with SHA-256 dedup, linking, library search."""

import hashlib
import json
import uuid

from sqlalchemy import func
from sqlalchemy.orm import Session

from config import settings
from models import Evidence, EvidenceLink
from storage import get_storage


BLOCKED_EXTENSIONS = {".exe", ".sh", ".bat", ".msi", ".zip", ".tar", ".rar", ".gz", ".7z"}
MAX_FILE_SIZE = settings.max_upload_size_mb * 1024 * 1024  # bytes


def compute_sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def validate_file(filename: str, size: int) -> str | None:
    """Return an error message if the file is invalid, else None."""
    ext = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext in BLOCKED_EXTENSIONS:
        return f"File type {ext} is not allowed"
    if size > MAX_FILE_SIZE:
        return f"File exceeds maximum size of {settings.max_upload_size_mb}MB"
    return None


def upload(
    db: Session,
    account_id: str,
    user_id: str | None,
    user_name: str,
    filename: str,
    content: bytes,
    content_type: str,
    description: str = "",
    tags: list[str] | None = None,
) -> tuple[Evidence, bool]:
    """Upload evidence with SHA-256 dedup.

    Returns (evidence_row, was_duplicate).
    If same sha256 exists in account, returns existing row without re-uploading.
    """
    sha = compute_sha256(content)

    # Check for dedup within this account
    existing = (
        db.query(Evidence)
        .filter(
            Evidence.account_id == account_id,
            Evidence.sha256 == sha,
            Evidence.deleted_at.is_(None),
        )
        .first()
    )
    if existing:
        return existing, True

    # Upload to storage
    storage = get_storage()
    key = f"{account_id}/{sha[:8]}_{uuid.uuid4().hex[:8]}_{filename}"
    storage.put(key, content, content_type)

    ev = Evidence(
        account_id=account_id,
        filename=filename,
        stored_filename=key,
        s3_key=key,
        file_size=len(content),
        content_type=content_type,
        sha256=sha,
        description=description,
        tags=json.dumps(tags or []),
        uploaded_by=user_name,
        uploaded_by_user_id=user_id,
    )
    db.add(ev)
    db.flush()
    return ev, False


def link(
    db: Session,
    evidence_id: str,
    entity_type: str,
    entity_id: str,
    link_type: str = "primary",
    user_id: str | None = None,
) -> EvidenceLink:
    """Link evidence to an entity. Idempotent on (evidence_id, entity_type, entity_id) while active."""
    existing = (
        db.query(EvidenceLink)
        .filter(
            EvidenceLink.evidence_id == evidence_id,
            EvidenceLink.entity_type == entity_type,
            EvidenceLink.entity_id == entity_id,
            EvidenceLink.unlinked_at.is_(None),
        )
        .first()
    )
    if existing:
        return existing

    el = EvidenceLink(
        evidence_id=evidence_id,
        entity_type=entity_type,
        entity_id=entity_id,
        link_type=link_type,
        linked_by_user_id=user_id,
    )
    db.add(el)
    db.flush()
    return el


def unlink(db: Session, link_id: str) -> EvidenceLink | None:
    """Soft unlink — sets unlinked_at. Returns the link or None if not found."""
    from datetime import datetime, timezone

    el = db.query(EvidenceLink).filter(EvidenceLink.id == link_id, EvidenceLink.unlinked_at.is_(None)).first()
    if not el:
        return None
    el.unlinked_at = datetime.now(timezone.utc)
    db.flush()
    return el


def get_for_entity(
    db: Session,
    account_id: str,
    entity_type: str,
    entity_id: str,
) -> list[dict]:
    """Get all evidence linked to a specific entity, with link info."""
    links = (
        db.query(EvidenceLink, Evidence)
        .join(Evidence, EvidenceLink.evidence_id == Evidence.id)
        .filter(
            Evidence.account_id == account_id,
            Evidence.deleted_at.is_(None),
            EvidenceLink.entity_type == entity_type,
            EvidenceLink.entity_id == entity_id,
            EvidenceLink.unlinked_at.is_(None),
        )
        .order_by(Evidence.uploaded_at.desc())
        .all()
    )
    return [{"evidence": ev, "link": lnk} for lnk, ev in links]


def search_library(
    db: Session,
    account_id: str,
    q: str = "",
    tags: list[str] | None = None,
    page: int = 1,
    per_page: int = 20,
) -> tuple[list[dict], int]:
    """Search the evidence library with optional filters.

    Returns (items_with_link_count, total_count).
    """
    query = db.query(Evidence).filter(
        Evidence.account_id == account_id,
        Evidence.deleted_at.is_(None),
    )

    if q:
        like_q = f"%{q}%"
        query = query.filter(
            (Evidence.filename.ilike(like_q))
            | (Evidence.description.ilike(like_q))
            | (Evidence.tags.ilike(like_q))
        )

    if tags:
        for tag in tags:
            query = query.filter(Evidence.tags.ilike(f'%"{tag}"%'))

    total = query.count()
    rows = query.order_by(Evidence.uploaded_at.desc()).offset((page - 1) * per_page).limit(per_page).all()

    # Get link counts
    results = []
    for ev in rows:
        link_count = (
            db.query(func.count(EvidenceLink.id))
            .filter(EvidenceLink.evidence_id == ev.id, EvidenceLink.unlinked_at.is_(None))
            .scalar()
        )
        results.append({"evidence": ev, "link_count": link_count})

    return results, total


def get_download_url(db: Session, evidence_id: str, account_id: str) -> tuple[str, str, bool] | None:
    """Get download URL for evidence.

    Returns (url_or_path, filename, is_signed_url) or None if not found.
    """
    ev = (
        db.query(Evidence)
        .filter(Evidence.id == evidence_id, Evidence.account_id == account_id, Evidence.deleted_at.is_(None))
        .first()
    )
    if not ev:
        return None

    storage = get_storage()
    key = ev.s3_key or ev.stored_filename
    url = storage.get_download_url(key, ev.filename, settings.s3_signed_url_expiry)

    # If S3 is configured, the URL is a signed URL; otherwise it's a filesystem path
    is_signed = bool(settings.s3_evidence_bucket)
    return url, ev.filename, is_signed


def soft_delete(db: Session, evidence_id: str, account_id: str) -> Evidence | None:
    """Soft delete evidence and unlink all active links."""
    from datetime import datetime, timezone

    ev = (
        db.query(Evidence)
        .filter(Evidence.id == evidence_id, Evidence.account_id == account_id, Evidence.deleted_at.is_(None))
        .first()
    )
    if not ev:
        return None

    now = datetime.now(timezone.utc)
    ev.deleted_at = now

    # Unlink all active links
    db.query(EvidenceLink).filter(
        EvidenceLink.evidence_id == evidence_id,
        EvidenceLink.unlinked_at.is_(None),
    ).update({"unlinked_at": now})

    db.flush()
    return ev


def get_tags(db: Session, account_id: str) -> list[str]:
    """Get all distinct tags used in the account."""
    rows = (
        db.query(Evidence.tags)
        .filter(Evidence.account_id == account_id, Evidence.deleted_at.is_(None))
        .all()
    )
    tag_set: set[str] = set()
    for (tags_json,) in rows:
        if tags_json:
            try:
                parsed = json.loads(tags_json)
                if isinstance(parsed, list):
                    tag_set.update(parsed)
            except (json.JSONDecodeError, TypeError):
                pass
    return sorted(tag_set)
