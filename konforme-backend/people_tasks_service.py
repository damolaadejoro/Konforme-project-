"""Service layer for Phase 4: People Tasks — Continuous Compliance.

Handles baseline instantiation, task completion, period rollover,
ISMS coverage computation, and pending instantiation consumption.
"""

import logging
from calendar import monthrange
from datetime import date, datetime, timezone

from sqlalchemy import func
from sqlalchemy.orm import Session

import audit_service
from models import (
    BusinessProcess,
    EvidenceLink,
    PendingPeopleTaskInstantiation,
    PeopleTask,
    PeopleTaskCompletion,
    User,
)
from scripts.seed_continuous_baseline import get_baseline_templates

logger = logging.getLogger(__name__)

# Fields whose update requires a change_reason and emits a material audit event
MATERIAL_FIELDS = {"frequency", "attestation_statement", "related_control_id", "next_due_date", "active"}

# Article 21(2) subsection labels (a-j)
ARTICLE_21_LABELS = {
    "a": "Risk analysis & IS policies",
    "b": "Incident handling",
    "c": "Business continuity & crisis mgmt",
    "d": "Supply chain security",
    "e": "Network & IS acquisition/development",
    "f": "Vulnerability handling & disclosure",
    "g": "Effectiveness assessment",
    "h": "Cybersecurity hygiene & training",
    "i": "Cryptography & encryption",
    "j": "HR security & access control",
}


def compute_period_key(frequency: str, ref_date: date | None = None) -> str:
    """Compute period key for the given frequency and reference date.

    Returns: "2026-04" (monthly), "2026-Q2" (quarterly), "2026" (annual), "one_off".
    """
    if frequency == "one_off":
        return "one_off"
    d = ref_date or date.today()
    if frequency == "monthly":
        return f"{d.year}-{d.month:02d}"
    if frequency == "quarterly":
        q = (d.month - 1) // 3 + 1
        return f"{d.year}-Q{q}"
    if frequency == "annual":
        return str(d.year)
    return "one_off"


def _compute_initial_due_date(frequency: str, today: date | None = None) -> date | None:
    """Compute first due date: end of current period."""
    if frequency == "one_off":
        return None
    d = today or date.today()
    if frequency == "monthly":
        _, last_day = monthrange(d.year, d.month)
        return date(d.year, d.month, last_day)
    if frequency == "quarterly":
        q = (d.month - 1) // 3 + 1
        end_month = q * 3
        _, last_day = monthrange(d.year, end_month)
        return date(d.year, end_month, last_day)
    if frequency == "annual":
        return date(d.year, 12, 31)
    return None


def _compute_next_due_date(frequency: str, current_due: date) -> date | None:
    """Advance due date to the next period."""
    if frequency == "one_off":
        return None
    if frequency == "monthly":
        if current_due.month == 12:
            y, m = current_due.year + 1, 1
        else:
            y, m = current_due.year, current_due.month + 1
        _, last_day = monthrange(y, m)
        return date(y, m, last_day)
    if frequency == "quarterly":
        m = current_due.month + 3
        y = current_due.year
        if m > 12:
            m -= 12
            y += 1
        _, last_day = monthrange(y, m)
        return date(y, m, last_day)
    if frequency == "annual":
        return date(current_due.year + 1, 12, 31)
    return None


def instantiate_baseline(
    db: Session,
    account_id: str,
    *,
    actor_user_id: str | None = None,
) -> dict:
    """Idempotent: load baseline YAML, create PeopleTask rows for any missing templates.

    Per-process templates (per_process=true) are instantiated once per critical
    business process, using composite baseline_template_id = "template_id::process_id".

    Returns {"created": int, "skipped": int}.
    """
    templates = get_baseline_templates()

    # Fetch existing baseline template IDs for this account
    existing_ids = set(
        row[0]
        for row in db.query(PeopleTask.baseline_template_id)
        .filter(
            PeopleTask.account_id == account_id,
            PeopleTask.baseline_template_id.isnot(None),
        )
        .all()
    )

    # Fetch critical business processes
    processes = (
        db.query(BusinessProcess)
        .filter(BusinessProcess.account_id == account_id, BusinessProcess.is_critical.is_(True))
        .all()
    )

    created = 0
    skipped = 0
    today = date.today()

    for tpl in templates:
        per_process = tpl.get("per_process", False)

        if per_process and processes:
            for bp in processes:
                composite_id = f"{tpl['template_id']}::{bp.id}"
                if composite_id in existing_ids:
                    skipped += 1
                    continue

                title = tpl["title"].replace("{critical_process}", bp.name)
                desc = tpl.get("description", "").replace("{critical_process}", bp.name)
                attestation = (tpl.get("attestation_statement") or "").replace("{critical_process}", bp.name)

                task = PeopleTask(
                    account_id=account_id,
                    title=title,
                    description=desc,
                    task_type=tpl["task_type"],
                    pdca_phase=tpl["pdca_phase"],
                    article_21_subsection=tpl["article_21_subsection"],
                    frequency=tpl["frequency"],
                    next_due_date=_compute_initial_due_date(tpl["frequency"], today),
                    related_control_id=tpl.get("related_control_id"),
                    related_process_id=bp.id,
                    requires_evidence=tpl.get("requires_evidence", False),
                    attestation_statement=attestation or None,
                    baseline_template_id=composite_id,
                )
                db.add(task)
                created += 1
        else:
            template_id = tpl["template_id"]
            if template_id in existing_ids:
                skipped += 1
                continue

            task = PeopleTask(
                account_id=account_id,
                title=tpl["title"],
                description=tpl.get("description", ""),
                task_type=tpl["task_type"],
                pdca_phase=tpl["pdca_phase"],
                article_21_subsection=tpl["article_21_subsection"],
                frequency=tpl["frequency"],
                next_due_date=_compute_initial_due_date(tpl["frequency"], today),
                related_control_id=tpl.get("related_control_id"),
                requires_evidence=tpl.get("requires_evidence", False),
                attestation_statement=tpl.get("attestation_statement"),
                baseline_template_id=template_id,
            )
            db.add(task)
            created += 1

    if created:
        audit_service.emit(
            db,
            account_id,
            "people_tasks.baseline_instantiated",
            actor_user_id=actor_user_id,
            entity_type="people_task",
            after_state={"created": created, "skipped": skipped, "process_count": len(processes)},
        )

    db.flush()
    return {"created": created, "skipped": skipped}


def complete_task(
    db: Session,
    task: PeopleTask,
    user: User,
    *,
    attestation_response: str | None = None,
    evidence_id: str | None = None,
) -> PeopleTaskCompletion:
    """Record a completion for the current period.

    Raises ValueError if already completed for this period.
    """
    period_key = compute_period_key(task.frequency)
    now = datetime.now(timezone.utc)

    # Check for existing completion
    existing = (
        db.query(PeopleTaskCompletion)
        .filter(
            PeopleTaskCompletion.people_task_id == task.id,
            PeopleTaskCompletion.user_id == user.id,
            PeopleTaskCompletion.period_key == period_key,
        )
        .first()
    )
    if existing:
        raise ValueError(f"Already completed for period {period_key}")

    completion = PeopleTaskCompletion(
        people_task_id=task.id,
        user_id=user.id,
        period_key=period_key,
        attested_at=now,
        attestation_response=attestation_response,
        evidence_id=evidence_id,
    )
    db.add(completion)
    db.flush()

    # Link evidence if provided
    if evidence_id:
        link = EvidenceLink(
            evidence_id=evidence_id,
            entity_type="people_task_completion",
            entity_id=completion.id,
            link_type="primary",
            linked_by_user_id=user.id,
        )
        db.add(link)

    audit_service.emit(
        db,
        task.account_id,
        "people_tasks.completed",
        actor_user_id=user.id,
        entity_type="people_task",
        entity_id=task.id,
        entity_label=task.title,
        after_state={
            "period_key": period_key,
            "has_evidence": bool(evidence_id),
            "has_attestation": bool(attestation_response),
        },
    )

    return completion


def consume_pending_instantiations(db: Session, account_id: str) -> int:
    """Drain PendingPeopleTaskInstantiation queue, creating PeopleTask per pending row.

    Returns number of tasks created.
    """
    pending = (
        db.query(PendingPeopleTaskInstantiation)
        .filter(
            PendingPeopleTaskInstantiation.account_id == account_id,
            PendingPeopleTaskInstantiation.status == "pending",
        )
        .all()
    )

    if not pending:
        return 0

    created = 0
    now = datetime.now(timezone.utc)

    for item in pending:
        task = PeopleTask(
            account_id=account_id,
            title=f"Ongoing compliance: {item.control_id}",
            description=f"Continuous compliance task spawned from remediation plan approval for control {item.control_id}.",
            task_type="attestation",
            pdca_phase="do",
            article_21_subsection="a",
            frequency="quarterly",
            next_due_date=_compute_initial_due_date("quarterly"),
            related_control_id=item.control_id,
            related_plan_id=item.source_plan_id,
            requires_evidence=False,
            attestation_statement=f"I confirm that control {item.control_id} remains implemented and effective.",
        )
        db.add(task)

        item.status = "instantiated"
        item.instantiated_at = now
        created += 1

    if created:
        audit_service.emit(
            db,
            account_id,
            "people_tasks.pending_consumed",
            entity_type="people_task",
            after_state={"created": created},
        )

    db.flush()
    return created


def get_isms_coverage(db: Session, account_id: str) -> dict:
    """Compute PDCA summary, Article 21 coverage (a-j), and health score.

    Returns an ISMSCoverageResponse-compatible dict.
    """
    today = date.today()

    # All active tasks
    tasks = (
        db.query(PeopleTask)
        .filter(PeopleTask.account_id == account_id, PeopleTask.active.is_(True))
        .all()
    )

    if not tasks:
        return {
            "pdcaSummary": {p: {"total": 0, "completed": 0, "rate": 0.0} for p in ["plan", "do", "check", "act"]},
            "article21Coverage": [
                {"subsection": s, "label": ARTICLE_21_LABELS[s], "taskCount": 0, "completionRate": 0.0, "status": "not_started"}
                for s in "abcdefghij"
            ],
            "overallHealthScore": 0.0,
            "overdueCount": 0,
            "totalActive": 0,
            "completedThisPeriod": 0,
        }

    task_ids = [t.id for t in tasks]

    # Get completions for current period per task
    completions_by_task: dict[str, int] = {}
    for t in tasks:
        pk = compute_period_key(t.frequency)
        count = (
            db.query(func.count(PeopleTaskCompletion.id))
            .filter(
                PeopleTaskCompletion.people_task_id == t.id,
                PeopleTaskCompletion.period_key == pk,
            )
            .scalar()
        )
        completions_by_task[t.id] = count or 0

    total_active = len(tasks)
    completed_this_period = sum(1 for c in completions_by_task.values() if c > 0)
    overdue_count = sum(
        1 for t in tasks
        if t.next_due_date and t.next_due_date < today and completions_by_task.get(t.id, 0) == 0
    )

    # PDCA summary
    pdca_summary = {}
    for phase in ["plan", "do", "check", "act"]:
        phase_tasks = [t for t in tasks if t.pdca_phase == phase]
        phase_completed = sum(1 for t in phase_tasks if completions_by_task.get(t.id, 0) > 0)
        pdca_summary[phase] = {
            "total": len(phase_tasks),
            "completed": phase_completed,
            "rate": round(phase_completed / len(phase_tasks), 2) if phase_tasks else 0.0,
        }

    # Article 21 coverage
    article_coverage = []
    for sub in "abcdefghij":
        sub_tasks = [t for t in tasks if t.article_21_subsection == sub]
        sub_completed = sum(1 for t in sub_tasks if completions_by_task.get(t.id, 0) > 0)
        rate = round(sub_completed / len(sub_tasks), 2) if sub_tasks else 0.0
        if not sub_tasks:
            status = "not_started"
        elif rate >= 0.8:
            status = "healthy"
        elif rate >= 0.4:
            status = "partial"
        else:
            status = "at_risk"

        article_coverage.append({
            "subsection": sub,
            "label": ARTICLE_21_LABELS[sub],
            "taskCount": len(sub_tasks),
            "completionRate": rate,
            "status": status,
        })

    # Health score: weighted average of completion rate across all tasks
    health = round(completed_this_period / total_active, 2) if total_active else 0.0

    return {
        "pdcaSummary": pdca_summary,
        "article21Coverage": article_coverage,
        "overallHealthScore": health,
        "overdueCount": overdue_count,
        "totalActive": total_active,
        "completedThisPeriod": completed_this_period,
    }


def roll_period(db: Session) -> dict:
    """Advance next_due_date for tasks whose current period has expired.

    Called by the daily scheduler. Returns {"rolled": int}.
    """
    today = date.today()
    tasks = (
        db.query(PeopleTask)
        .filter(
            PeopleTask.active.is_(True),
            PeopleTask.next_due_date.isnot(None),
            PeopleTask.next_due_date < today,
            PeopleTask.frequency != "one_off",
        )
        .all()
    )

    rolled = 0
    for task in tasks:
        new_due = _compute_next_due_date(task.frequency, task.next_due_date)
        if new_due:
            task.next_due_date = new_due
            rolled += 1

    if rolled:
        db.flush()
        logger.info("Rolled %d people task periods", rolled)

    return {"rolled": rolled}


def get_task_period_status(
    db: Session, task: PeopleTask, user_id: str | None = None
) -> str:
    """Return current period status for a task: 'completed', 'overdue', or 'pending'."""
    pk = compute_period_key(task.frequency)
    query = db.query(PeopleTaskCompletion).filter(
        PeopleTaskCompletion.people_task_id == task.id,
        PeopleTaskCompletion.period_key == pk,
    )
    if user_id:
        query = query.filter(PeopleTaskCompletion.user_id == user_id)

    if query.first():
        return "completed"
    if task.next_due_date and task.next_due_date < date.today():
        return "overdue"
    return "pending"
