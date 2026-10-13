"""Audit service with DB persistence and tamper-evident hash chain.

Every compliance-relevant action writes to audit_log via emit().
The hash chain provides tamper evidence for ISO 27001 / NIS2 compliance.
"""

import hashlib
import json
import uuid
from datetime import datetime, timezone

from database import Session
from models import AuditLog

GENESIS_HASH = "0" * 64


def _canonical(obj: dict | None) -> str:
    """Deterministic JSON serialization for hash computation."""
    if obj is None:
        return ""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), default=str)


def _compute_hash(
    row_id: int,
    account_id: str | None,
    event_type: str,
    occurred_at: str,
    actor_user_id: str | None,
    entity_type: str | None,
    entity_id: str | None,
    before_state: str | None,
    after_state: str | None,
    change_reason: str | None,
    prev_hash: str,
) -> str:
    """Compute SHA-256 hash for a single audit log row."""
    payload = (
        f"{prev_hash}|{row_id}|{account_id or ''}|{event_type}|{occurred_at}"
        f"|{actor_user_id or ''}|{entity_type or ''}|{entity_id or ''}"
        f"|{before_state or ''}|{after_state or ''}|{change_reason or ''}"
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def emit(
    db: Session,
    account_id: str | None,
    event_type: str,
    *,
    actor_user_id: str | None = None,
    actor_email: str | None = None,
    actor_ip: str | None = None,
    entity_type: str | None = None,
    entity_id: str | None = None,
    entity_label: str | None = None,
    before_state: dict | None = None,
    after_state: dict | None = None,
    change_reason: str | None = None,
    is_material: bool = False,
    correlation_id: str | None = None,
    metadata: dict | None = None,
) -> AuditLog:
    """Insert an audit event with hash chain integrity.

    Must be called within an active DB transaction. The event is committed
    together with the business change — ensuring atomicity.
    """
    now = datetime.now(timezone.utc)

    # Get previous hash for this account's chain
    prev_row = db.last(AuditLog, account_id)
    prev_hash = prev_row.hash if prev_row else GENESIS_HASH

    # Derive event_category from the first segment of event_type
    event_category = event_type.split(".")[0] if "." in event_type else event_type

    before_json = json.dumps(before_state, default=str) if before_state else None
    after_json = json.dumps(after_state, default=str) if after_state else None

    log = AuditLog(
        account_id=account_id,
        event_type=event_type,
        event_category=event_category,
        actor_user_id=actor_user_id,
        actor_email=actor_email,
        actor_ip=actor_ip,
        entity_type=entity_type,
        entity_id=entity_id,
        entity_label=entity_label,
        correlation_id=correlation_id or str(uuid.uuid4()),
        before_state=before_json,
        after_state=after_json,
        change_reason=change_reason,
        is_material=is_material,
        metadata_json=json.dumps(metadata, default=str) if metadata else None,
        occurred_at=now,
        prev_hash=prev_hash,
        hash="",  # placeholder — computed below from the row ID
    )
    db.add(log)

    # Compute the tamper-evident hash
    log.hash = _compute_hash(
        row_id=log.id,
        account_id=account_id,
        event_type=event_type,
        occurred_at=now.isoformat(),
        actor_user_id=actor_user_id,
        entity_type=entity_type,
        entity_id=entity_id,
        before_state=before_json,
        after_state=after_json,
        change_reason=change_reason,
        prev_hash=prev_hash,
    )

    return log


def verify_chain(db: Session, account_id: str) -> dict:
    """Walk the hash chain for an account and verify integrity.

    Returns {"valid": bool, "total": int, "checked": int, "first_broken_at": int | None}.
    """
    rows = sorted(db.list(AuditLog, account_id), key=lambda r: r.id)

    if not rows:
        return {"valid": True, "total": 0, "checked": 0, "first_broken_at": None}

    expected_prev = GENESIS_HASH
    for row in rows:
        # Check prev_hash linkage
        if (row.prev_hash or GENESIS_HASH) != expected_prev:
            return {
                "valid": False,
                "total": len(rows),
                "checked": row.id,
                "first_broken_at": row.id,
            }

        # Recompute hash and verify
        expected_hash = _compute_hash(
            row_id=row.id,
            account_id=row.account_id,
            event_type=row.event_type,
            occurred_at=row.occurred_at.isoformat() if row.occurred_at else "",
            actor_user_id=row.actor_user_id,
            entity_type=row.entity_type,
            entity_id=row.entity_id,
            before_state=row.before_state,
            after_state=row.after_state,
            change_reason=row.change_reason,
            prev_hash=row.prev_hash or GENESIS_HASH,
        )
        if row.hash != expected_hash:
            return {
                "valid": False,
                "total": len(rows),
                "checked": row.id,
                "first_broken_at": row.id,
            }

        expected_prev = row.hash

    return {"valid": True, "total": len(rows), "checked": len(rows), "first_broken_at": None}
