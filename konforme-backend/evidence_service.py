"""Evidence business logic: upload with SHA-256 dedup, linking, library search."""

import hashlib
import json
import uuid

from config import settings
from database import Session
from models import BaseControl, BusinessProcess, Evidence, EvidenceLink, PeopleTask, RemediationTask
from storage import get_storage
from store import order_by


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
    existing = next(
        (e for e in order_by(db.list(Evidence, account_id), "uploaded_at")
         if e.sha256 == sha and e.deleted_at is None),
        None,
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
    from datetime import datetime, timezone

    ev = db.get(Evidence, evidence_id)
    if ev is None:
        raise LookupError(f"Evidence {evidence_id} not found")

    existing = db.get_by_key(
        EvidenceLink, ev.account_id, evidence_id=evidence_id, entity_type=entity_type, entity_id=entity_id
    )
    if existing and existing.unlinked_at is None:
        return existing
    if existing:
        # One row per (evidence, entity): re-linking reactivates the soft-unlinked row
        existing.unlinked_at = None
        existing.link_type = link_type
        existing.linked_by_user_id = user_id
        existing.linked_at = datetime.now(timezone.utc)
        return existing

    el = EvidenceLink(
        account_id=ev.account_id,
        evidence_id=evidence_id,
        entity_type=entity_type,
        entity_id=entity_id,
        link_type=link_type,
        linked_by_user_id=user_id,
    )
    db.add(el)
    return el


def unlink(db: Session, link_id: str, account_id: str) -> EvidenceLink | None:
    """Soft unlink — sets unlinked_at. Returns the link or None if not found in this account."""
    from datetime import datetime, timezone

    el = next(
        (lnk for lnk in db.list(EvidenceLink, account_id) if lnk.id == link_id and lnk.unlinked_at is None),
        None,
    )
    if not el:
        return None
    el.unlinked_at = datetime.now(timezone.utc)
    return el


def get_for_entity(
    db: Session,
    account_id: str,
    entity_type: str,
    entity_id: str,
) -> list[dict]:
    """Get all evidence linked to a specific entity, with link info."""
    evidence_by_id = {e.id: e for e in db.list(Evidence, account_id) if e.deleted_at is None}
    pairs = [
        (lnk, evidence_by_id[lnk.evidence_id])
        for lnk in db.list(EvidenceLink, account_id)
        if lnk.entity_type == entity_type
        and lnk.entity_id == entity_id
        and lnk.unlinked_at is None
        and lnk.evidence_id in evidence_by_id
    ]
    pairs.sort(key=lambda p: p[1].uploaded_at, reverse=True)
    return [{"evidence": ev, "link": lnk} for lnk, ev in pairs]


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
    matches = [e for e in db.list(Evidence, account_id) if e.deleted_at is None]

    def contains(value: str | None, needle: str) -> bool:
        # SQL ILIKE '%needle%'
        return needle.lower() in (value or "").lower()

    if q:
        matches = [e for e in matches if contains(e.filename, q) or contains(e.description, q) or contains(e.tags, q)]

    if tags:
        for tag in tags:
            matches = [e for e in matches if contains(e.tags, f'"{tag}"')]

    total = len(matches)
    start = (page - 1) * per_page
    rows = order_by(matches, "uploaded_at", desc=True)[start:start + per_page]

    # Get link counts and linked entity details
    ev_ids = [ev.id for ev in rows]
    links_by_evidence: dict[str, list] = {eid: [] for eid in ev_ids}
    if ev_ids:
        wanted = set(ev_ids)
        active_links = [
            lnk for lnk in db.list(EvidenceLink, account_id)
            if lnk.evidence_id in wanted and lnk.unlinked_at is None
        ]
        for lnk in active_links:
            links_by_evidence.setdefault(lnk.evidence_id, []).append(lnk)

    # Batch-resolve entity names
    entity_names = _resolve_entity_names(db, account_id, active_links if ev_ids else [])

    results = []
    for ev in rows:
        ev_links = links_by_evidence.get(ev.id, [])
        linked_entities = []
        for lnk in ev_links:
            name = entity_names.get((lnk.entity_type, lnk.entity_id), lnk.entity_id)
            linked_entities.append({
                "link_id": lnk.id,
                "entity_type": lnk.entity_type,
                "entity_id": lnk.entity_id,
                "entity_name": name,
            })
        results.append({
            "evidence": ev,
            "link_count": len(ev_links),
            "linked_entities": linked_entities,
        })

    return results, total


def _resolve_entity_names(db: Session, account_id: str, links: list[EvidenceLink]) -> dict[tuple[str, str], str]:
    """Batch-resolve human-readable names for linked entities."""
    names: dict[tuple[str, str], str] = {}
    by_type: dict[str, set[str]] = {}
    for lnk in links:
        by_type.setdefault(lnk.entity_type, set()).add(lnk.entity_id)

    # Controls
    control_ids = by_type.get("control", set())
    if control_ids:
        for c in db.all(BaseControl):
            if c.control_id in control_ids:
                names[("control", c.control_id)] = c.title

    # Remediation tasks
    rt_ids = by_type.get("remediation_task", set())
    if rt_ids:
        for t in db.list(RemediationTask, account_id):
            if t.id in rt_ids:
                names[("remediation_task", t.id)] = t.title

    # People tasks
    pt_ids = by_type.get("people_task", set())
    if pt_ids:
        for t in db.list(PeopleTask, account_id):
            if t.id in pt_ids:
                names[("people_task", t.id)] = t.title

    # Business processes
    bp_ids = by_type.get("process", set())
    if bp_ids:
        for bp in db.list(BusinessProcess, account_id):
            if bp.id in bp_ids:
                names[("process", bp.id)] = bp.name

    # Assessment answers — no separate table with title, use question_id
    for aid in by_type.get("assessment_answer", set()):
        names[("assessment_answer", aid)] = f"Assessment Q: {aid}"

    return names


def get_download_url(db: Session, evidence_id: str, account_id: str) -> tuple[str, str, bool] | None:
    """Get download URL for evidence.

    Returns (url_or_path, filename, is_signed_url) or None if not found.
    """
    ev = db.get_by_key(Evidence, account_id, id=evidence_id)
    if ev and ev.deleted_at is not None:
        ev = None
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

    ev = db.get_by_key(Evidence, account_id, id=evidence_id)
    if ev and ev.deleted_at is not None:
        ev = None
    if not ev:
        return None

    now = datetime.now(timezone.utc)
    ev.deleted_at = now

    # Unlink all active links
    for lnk in db.list(EvidenceLink, account_id):
        if lnk.evidence_id == evidence_id and lnk.unlinked_at is None:
            lnk.unlinked_at = now

    return ev


def get_tags(db: Session, account_id: str) -> list[str]:
    """Get all distinct tags used in the account."""
    rows = [e.tags for e in db.list(Evidence, account_id) if e.deleted_at is None]
    tag_set: set[str] = set()
    for tags_json in rows:
        if tags_json:
            try:
                parsed = json.loads(tags_json)
                if isinstance(parsed, list):
                    tag_set.update(parsed)
            except (json.JSONDecodeError, TypeError):
                pass
    return sorted(tag_set)
