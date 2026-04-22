"""Audit log endpoints: paginated list, single event, chain verification."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from auth import enforce_account_access, get_current_account, get_current_user
from database import get_db
from models import Account, AuditLog, User, UserRole
from schemas import AuditLogEntry, AuditLogResponse, ChainVerificationResponse

router = APIRouter()


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

    query = db.query(AuditLog).filter(AuditLog.account_id == account_id)

    if event_type:
        query = query.filter(AuditLog.event_type == event_type)
    if entity_type:
        query = query.filter(AuditLog.entity_type == entity_type)
    if entity_id:
        query = query.filter(AuditLog.entity_id == entity_id)
    if actor_user_id:
        query = query.filter(AuditLog.actor_user_id == actor_user_id)
    if q:
        like_q = f"%{q}%"
        query = query.filter(
            (AuditLog.entity_label.ilike(like_q)) | (AuditLog.actor_email.ilike(like_q))
        )
    if date_from:
        query = query.filter(AuditLog.occurred_at >= date_from)
    if date_to:
        query = query.filter(AuditLog.occurred_at <= date_to)

    total = query.count()
    rows = (
        query.order_by(AuditLog.occurred_at.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )

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

    row = db.query(AuditLog).filter(
        AuditLog.id == event_id, AuditLog.account_id == account_id,
    ).first()
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
    query = db.query(AuditLog).filter(AuditLog.actor_user_id == user.id)
    total = query.count()
    rows = (
        query.order_by(AuditLog.occurred_at.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )
    return AuditLogResponse(
        items=[_row_to_entry(r) for r in rows],
        total=total,
        page=page,
        perPage=per_page,
    )
