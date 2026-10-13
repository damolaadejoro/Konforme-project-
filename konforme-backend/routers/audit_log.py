"""Audit log endpoints: paginated list, single event, chain verification."""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query

from auth import enforce_account_access, get_current_account, get_current_user
from database import Session, get_db
from models import Account, AuditLog, User, UserRole
from schemas import AuditLogEntry, AuditLogResponse, ChainVerificationResponse
from store import order_by

router = APIRouter()


def _parse_bound(value: str) -> datetime:
    """Parse a date/datetime filter like PostgreSQL would (naive = UTC)."""
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        raise HTTPException(status_code=422, detail=f"Invalid date: {value}")
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def _page(rows: list[AuditLog], page: int, per_page: int) -> tuple[list[AuditLog], int]:
    ordered = order_by(rows, "occurred_at", desc=True)
    start = (page - 1) * per_page
    return ordered[start:start + per_page], len(ordered)


def _row_to_entry(row: AuditLog) -> AuditLogEntry:
    return AuditLogEntry(
        id=row.id,
        eventType=row.event_type,
        eventCategory=row.event_category,
        actorEmail=row.actor_email,
        actorUserId=row.actor_user_id,
        entityType=row.entity_type,
        entityId=row.entity_id,
        entityLabel=row.entity_label,
        correlationId=row.correlation_id,
        occurredAt=row.occurred_at.isoformat() if row.occurred_at else "",
    )


@router.get("/audit/{account_id}", response_model=AuditLogResponse)
def list_audit_log(
    account_id: str,
    event_type: str = Query("", description="Filter by event type"),
    entity_type: str = Query("", description="Filter by entity type"),
    entity_id: str = Query("", description="Filter by entity id"),
    actor_user_id: str = Query("", description="Filter by actor user id"),
    q: str = Query("", description="Search entity_label, actor_email"),
    date_from: str = Query("", description="ISO date from"),
    date_to: str = Query("", description="ISO date to"),
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    account: Account = Depends(get_current_account),
    db: Session = Depends(get_db),
):
    """List audit log entries for an account with optional filters."""
    enforce_account_access(account, account_id)

    rows = db.list(AuditLog, account_id)

    if event_type:
        rows = [r for r in rows if r.event_type == event_type]
    if entity_type:
        rows = [r for r in rows if r.entity_type == entity_type]
    if entity_id:
        rows = [r for r in rows if r.entity_id == entity_id]
    if actor_user_id:
        rows = [r for r in rows if r.actor_user_id == actor_user_id]
    if q:
        needle = q.lower()
        rows = [
            r for r in rows
            if needle in (r.entity_label or "").lower() or needle in (r.actor_email or "").lower()
        ]
    if date_from:
        lower = _parse_bound(date_from)
        rows = [r for r in rows if r.occurred_at and r.occurred_at >= lower]
    if date_to:
        upper = _parse_bound(date_to)
        rows = [r for r in rows if r.occurred_at and r.occurred_at <= upper]

    rows, total = _page(rows, page, per_page)

    return AuditLogResponse(
        items=[_row_to_entry(r) for r in rows],
        total=total,
        page=page,
        perPage=per_page,
    )


@router.get("/audit/{account_id}/verify", response_model=ChainVerificationResponse)
def verify_audit_chain(
    account_id: str,
    account: Account = Depends(get_current_account),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Verify tamper-evident hash chain integrity. Admin/owner only."""
    enforce_account_access(account, account_id)
    if user.role not in (UserRole.owner.value, UserRole.admin.value):
        raise HTTPException(status_code=403, detail="Only admins can verify the audit chain")

    import audit_service
    result = audit_service.verify_chain(db, account_id)
    return ChainVerificationResponse(
        valid=result["valid"],
        total=result["total"],
        checked=result["checked"],
        firstBrokenAt=result["first_broken_at"],
    )


@router.get("/audit/{account_id}/{event_id}", response_model=AuditLogEntry)
def get_audit_event(
    account_id: str,
    event_id: int,
    account: Account = Depends(get_current_account),
    db: Session = Depends(get_db),
):
    """Get a single audit log event."""
    enforce_account_access(account, account_id)

    row = db.get_by_key(AuditLog, account_id, id=event_id)
    if not row:
        raise HTTPException(status_code=404, detail="Audit event not found")
    return _row_to_entry(row)


@router.get("/me/activity", response_model=AuditLogResponse)
def get_my_activity(
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get current user's activity across all accounts."""
    # A user's events are in their account's log, plus account-less events
    candidates = db.list(AuditLog, user.account_id) + db.list(AuditLog, None)
    rows, total = _page([r for r in candidates if r.actor_user_id == user.id], page, per_page)
    return AuditLogResponse(
        items=[_row_to_entry(r) for r in rows],
        total=total,
        page=page,
        perPage=per_page,
    )
