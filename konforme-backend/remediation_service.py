"""Remediation service: plan CRUD, task close/dismiss/reschedule, auto-creation, chronic slip detection."""

from datetime import date, datetime, timedelta, timezone

import audit_service
from database import Session
from models import (
    AssessmentQuestionControl,
    BaseControl,
    Evidence,
    PendingPeopleTaskInstantiation,
    RemediationPlan,
    RemediationPlanLink,
    RemediationPlanMilestone,
    RemediationTask,
)
from store import order_by


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


# ---------------------------------------------------------------------------
# Plan CRUD
# ---------------------------------------------------------------------------


def create_plan(
    db: Session,
    account_id: str,
    title: str,
    description: str,
    treatment_type: str,
    target_date: date | None,
    linked_entities: list[dict],
    initial_task_ids: list[str],
    actor_user_id: str | None = None,
    actor_email: str | None = None,
) -> RemediationPlan:
    plan = RemediationPlan(
        account_id=account_id,
        title=title,
        description=description,
        treatment_type=treatment_type,
        target_date=target_date,
        created_by_user_id=actor_user_id,
    )
    db.add(plan)

    for ent in linked_entities:
        db.add(RemediationPlanLink(
            plan_id=plan.id,
            entity_type=ent["entity_type"],
            entity_id=ent["entity_id"],
        ))

    if initial_task_ids:
        wanted = set(initial_task_ids)
        for t in db.list(RemediationTask, account_id):
            if t.id in wanted:
                t.plan_id = plan.id

    audit_service.emit(
        db, account_id, "remediation.plan_create",
        actor_user_id=actor_user_id,
        actor_email=actor_email,
        entity_type="remediation_plan",
        entity_id=plan.id,
        entity_label=title,
        after_state={"treatment_type": treatment_type, "status": "draft"},
    )
    return plan


def update_plan(
    db: Session,
    plan: RemediationPlan,
    updates: dict,
    change_reason: str | None = None,
    actor_user_id: str | None = None,
    actor_email: str | None = None,
) -> RemediationPlan:
    material_fields = {"treatment_type", "target_date"}
    changed_material = any(k in material_fields for k, v in updates.items() if v is not None)

    before = {
        "title": plan.title,
        "description": plan.description,
        "treatment_type": plan.treatment_type,
        "target_date": str(plan.target_date) if plan.target_date else None,
    }

    for key, val in updates.items():
        if val is not None and hasattr(plan, key):
            setattr(plan, key, val)

    audit_service.emit(
        db, plan.account_id, "remediation.plan_update",
        actor_user_id=actor_user_id,
        actor_email=actor_email,
        entity_type="remediation_plan",
        entity_id=plan.id,
        entity_label=plan.title,
        before_state=before,
        after_state=updates,
        change_reason=change_reason,
        is_material=changed_material,
    )
    return plan


def approve_plan(
    db: Session,
    plan: RemediationPlan,
    actor_user_id: str,
    actor_email: str | None = None,
) -> RemediationPlan:
    plan.status = "approved"
    plan.approved_by_user_id = actor_user_id
    plan.approved_at = _utcnow()

    audit_service.emit(
        db, plan.account_id, "remediation.plan_approve",
        actor_user_id=actor_user_id,
        actor_email=actor_email,
        entity_type="remediation_plan",
        entity_id=plan.id,
        entity_label=plan.title,
        is_material=True,
    )
    return plan


def reject_plan(
    db: Session,
    plan: RemediationPlan,
    reason: str,
    actor_user_id: str,
    actor_email: str | None = None,
) -> RemediationPlan:
    plan.status = "rejected"
    plan.rejected_by_user_id = actor_user_id
    plan.rejected_at = _utcnow()
    plan.rejection_reason = reason

    audit_service.emit(
        db, plan.account_id, "remediation.plan_reject",
        actor_user_id=actor_user_id,
        actor_email=actor_email,
        entity_type="remediation_plan",
        entity_id=plan.id,
        entity_label=plan.title,
        change_reason=reason,
        is_material=True,
    )
    return plan


# ---------------------------------------------------------------------------
# Milestones
# ---------------------------------------------------------------------------


def add_milestone(
    db: Session,
    plan: RemediationPlan,
    title: str,
    description: str = "",
    target_date: date | None = None,
    display_order: int = 0,
) -> RemediationPlanMilestone:
    ms = RemediationPlanMilestone(
        plan_id=plan.id,
        title=title,
        description=description,
        target_date=target_date,
        display_order=display_order,
    )
    db.add(ms)
    return ms


def update_milestone(ms: RemediationPlanMilestone, updates: dict) -> RemediationPlanMilestone:
    for key, val in updates.items():
        if val is not None and hasattr(ms, key):
            setattr(ms, key, val)
    return ms


def complete_milestone(ms: RemediationPlanMilestone) -> RemediationPlanMilestone:
    ms.completed_at = _utcnow()
    return ms


# ---------------------------------------------------------------------------
# Task close / dismiss / reschedule
# ---------------------------------------------------------------------------


def close_task(
    db: Session,
    task: RemediationTask,
    closure_evidence_id: str | None = None,
    closure_note: str | None = None,
    actor_user_id: str | None = None,
    actor_email: str | None = None,
) -> RemediationTask:
    now = _utcnow()
    task.status = "completed"
    task.completed_at = now
    task.closure_evidence_id = closure_evidence_id
    task.closure_note = closure_note
    task.closed_by_user_id = actor_user_id

    audit_service.emit(
        db, task.account_id, "remediation.task_close",
        actor_user_id=actor_user_id,
        actor_email=actor_email,
        entity_type="remediation_task",
        entity_id=task.id,
        entity_label=task.title,
        after_state={
            "closure_evidence_id": closure_evidence_id,
            "closure_note": closure_note,
        },
        is_material=True,
    )

    # If the task targets a people-control, enqueue for Phase 4
    if task.related_control_id:
        base = db.get_by_key(BaseControl, control_id=task.related_control_id)
        if base and base.is_people_control:
            db.add(PendingPeopleTaskInstantiation(
                account_id=task.account_id,
                control_id=task.related_control_id,
                source_plan_id=task.plan_id,
                source_task_id=task.id,
            ))

    return task


def dismiss_task(
    db: Session,
    task: RemediationTask,
    reason: str,
    actor_user_id: str | None = None,
    actor_email: str | None = None,
) -> RemediationTask:
    task.status = "dismissed"
    task.dismissed_reason = reason
    task.dismissed_by_user_id = actor_user_id
    task.dismissed_at = _utcnow()

    audit_service.emit(
        db, task.account_id, "remediation.task_dismiss",
        actor_user_id=actor_user_id,
        actor_email=actor_email,
        entity_type="remediation_task",
        entity_id=task.id,
        entity_label=task.title,
        change_reason=reason,
    )
    return task


def bulk_dismiss(
    db: Session,
    account_id: str,
    task_ids: list[str],
    reason: str,
    actor_user_id: str | None = None,
    actor_email: str | None = None,
) -> int:
    wanted = set(task_ids)
    tasks = [
        t for t in db.list(RemediationTask, account_id)
        if t.id in wanted and t.status in ("open", "in_progress")
    ]

    now = _utcnow()
    for task in tasks:
        task.status = "dismissed"
        task.dismissed_reason = reason
        task.dismissed_by_user_id = actor_user_id
        task.dismissed_at = now

        audit_service.emit(
            db, account_id, "remediation.task_dismiss",
            actor_user_id=actor_user_id,
            actor_email=actor_email,
            entity_type="remediation_task",
            entity_id=task.id,
            entity_label=task.title,
            change_reason=reason,
        )
    return len(tasks)


def reschedule_task(
    db: Session,
    task: RemediationTask,
    new_due_date: date,
    reason: str,
    category: str = "other",
    actor_user_id: str | None = None,
    actor_email: str | None = None,
) -> RemediationTask:
    old_due = task.due_date

    # Preserve original due date on first reschedule
    if task.reschedule_count == 0 and task.due_date:
        task.original_due_date = task.due_date

    task.due_date = new_due_date
    task.reschedule_count = (task.reschedule_count or 0) + 1

    audit_service.emit(
        db, task.account_id, "remediation.task_reschedule",
        actor_user_id=actor_user_id,
        actor_email=actor_email,
        entity_type="remediation_task",
        entity_id=task.id,
        entity_label=task.title,
        before_state={"due_date": str(old_due) if old_due else None},
        after_state={
            "due_date": str(new_due_date),
            "reason": reason,
            "category": category,
            "reschedule_count": task.reschedule_count,
        },
    )
    return task


def is_chronic_slip(task: RemediationTask) -> bool:
    """True if reschedule_count >= 3 OR cumulative extension >= 100% of original duration."""
    if (task.reschedule_count or 0) >= 3:
        return True

    if task.original_due_date and task.due_date and task.created_at:
        original_duration = (task.original_due_date - task.created_at.date()).days
        if original_duration > 0:
            cumulative_extension = (task.due_date - task.original_due_date).days
            if cumulative_extension >= original_duration:
                return True
    return False


# ---------------------------------------------------------------------------
# Auto-create tasks from assessment answers
# ---------------------------------------------------------------------------


def auto_create_tasks(
    db: Session,
    account_id: str,
    assessment_version_id: str,
    responses: list,
    actor_user_id: str | None = None,
    actor_email: str | None = None,
) -> list[RemediationTask]:
    """Create remediation tasks for assessment answers with maturity_level < 2."""
    from assessment_questions import QUESTION_MAP

    created = []
    task_index = 0  # counter for staggering within this batch

    # Get all question-control mappings
    mappings = order_by(db.all(AssessmentQuestionControl), "created_at")  # seed order, as before
    account_tasks = db.list(RemediationTask, account_id)
    mapping_by_q: dict[str, list[AssessmentQuestionControl]] = {}
    for m in mappings:
        mapping_by_q.setdefault(m.question_id, []).append(m)

    for resp in responses:
        q_id = resp.question_id
        level = resp.maturity_level

        # Skip compliant answers (level >= 2 or N/A)
        if level is None or level >= 2:
            continue

        # Skip if open/in_progress task already exists for this question
        existing = next(
            (t for t in account_tasks if t.question_id == q_id and t.status in ("open", "in_progress")), None
        )
        if existing:
            continue

        q_data = QUESTION_MAP.get(q_id)
        q_text = q_data["question"][:400] if q_data else q_id
        severity = q_data.get("severity", "medium") if q_data else "medium"
        priority = _severity_to_priority(severity)
        due = _smart_due_date(severity, task_index)
        task_index += 1

        # Get first mapped control (if any)
        q_mappings = mapping_by_q.get(q_id, [])
        control_id = q_mappings[0].control_id if q_mappings else None

        task = RemediationTask(
            account_id=account_id,
            question_id=q_id,
            title=f"Remediate: {q_text}"[:500],
            description=f"Auto-generated from assessment (maturity level {level}/4).",
            status="open",
            priority=priority,
            severity=severity,
            auto_generated=True,
            due_date=due,
            original_due_date=due,
            related_control_id=control_id,
            related_assessment_answer_id=resp.id,
        )
        db.add(task)
        account_tasks.append(task)

        audit_service.emit(
            db, account_id, "remediation.auto_create",
            actor_user_id=actor_user_id,
            actor_email=actor_email,
            entity_type="remediation_task",
            entity_id=task.id,
            entity_label=task.title,
            after_state={
                "question_id": q_id,
                "maturity_level": level,
                "severity": severity,
                "control_id": control_id,
            },
        )
        created.append(task)

    return created


# ---------------------------------------------------------------------------
# Auto-create task from control status change
# ---------------------------------------------------------------------------


def _smart_due_date(severity: str, display_order: int) -> date:
    """Stagger due dates by severity and order within severity band.

    Phase 1 (30-45 days): Critical controls — foundational security gaps
    Phase 2 (45-75 days): High priority — core compliance requirements
    Phase 3 (75-120 days): Medium priority — supporting controls
    Within each phase, tasks are spread 3 days apart by display_order.
    """
    base_days = {"critical": 30, "high": 45, "medium": 75}.get(severity, 75)
    stagger = (display_order % 15) * 3  # spread up to ~45 days within band
    return date.today() + timedelta(days=base_days + stagger)


def _severity_to_priority(severity: str) -> str:
    return {"critical": "high", "high": "high", "medium": "medium"}.get(severity, "medium")


def auto_create_task_for_control(
    db: Session,
    account_id: str,
    control_id: str,
    control_status: str,
    actor_user_id: str | None = None,
    actor_email: str | None = None,
) -> RemediationTask | None:
    """Create a remediation task when a control is set to Planned or Not Started."""
    from models import BaseControl

    # Skip if open/in_progress task already exists for this control
    existing = next(
        (t for t in db.list(RemediationTask, account_id)
         if t.related_control_id == control_id and t.status in ("open", "in_progress")),
        None,
    )
    if existing:
        return None

    # Get control metadata for smart scheduling
    base = db.get_by_key(BaseControl, control_id=control_id)
    title = base.title if base else control_id
    severity = base.severity if base else "medium"
    display_order = base.display_order if base else 0
    priority = _severity_to_priority(severity)
    due = _smart_due_date(severity, display_order)

    task = RemediationTask(
        account_id=account_id,
        question_id=f"ctrl:{control_id}",
        title=f"Implement: {title}"[:500],
        description=f"Auto-generated — control status set to '{control_status}'.",
        status="open",
        priority=priority,
        severity=severity,
        auto_generated=True,
        due_date=due,
        original_due_date=due,
        related_control_id=control_id,
    )
    db.add(task)

    audit_service.emit(
        db, account_id, "remediation.auto_create",
        actor_user_id=actor_user_id,
        actor_email=actor_email,
        entity_type="remediation_task",
        entity_id=task.id,
        after_state={
            "control_id": control_id,
            "control_status": control_status,
        },
    )
    return task


# ---------------------------------------------------------------------------
# Auto-create task for a single assessment question (on auto-save)
# ---------------------------------------------------------------------------


def auto_create_tasks_for_single_question(
    db: Session,
    account_id: str,
    question_id: str,
    maturity_level: int,
    actor_user_id: str | None = None,
    actor_email: str | None = None,
) -> RemediationTask | None:
    """Create a remediation task for a single assessment answer with maturity < 2."""
    from assessment_questions import QUESTION_MAP

    # Skip if open/in_progress task already exists
    existing = next(
        (t for t in db.list(RemediationTask, account_id)
         if t.question_id == question_id and t.status in ("open", "in_progress")),
        None,
    )
    if existing:
        return None

    q_data = QUESTION_MAP.get(question_id)
    q_text = q_data["question"][:400] if q_data else question_id
    severity = q_data.get("severity", "medium") if q_data else "medium"

    # Get mapped control
    q_mappings = order_by(
        [m for m in db.all(AssessmentQuestionControl) if m.question_id == question_id], "created_at"
    )
    control_id = q_mappings[0].control_id if q_mappings else None

    priority = _severity_to_priority(severity)
    due = _smart_due_date(severity, 0)
    task = RemediationTask(
        account_id=account_id,
        question_id=question_id,
        title=f"Remediate: {q_text}"[:500],
        description=f"Auto-generated from assessment (maturity level {maturity_level}/4).",
        status="open",
        priority=priority,
        severity=severity,
        auto_generated=True,
        due_date=due,
        original_due_date=due,
        related_control_id=control_id,
    )
    db.add(task)

    audit_service.emit(
        db, account_id, "remediation.auto_create",
        actor_user_id=actor_user_id,
        actor_email=actor_email,
        entity_type="remediation_task",
        entity_id=task.id,
        entity_label=task.title,
        after_state={"question_id": question_id, "maturity_level": maturity_level},
    )
    return task


# ---------------------------------------------------------------------------
# Auto-close tasks when controls/assessment answers become compliant
# ---------------------------------------------------------------------------


def auto_close_tasks_for_control(
    db: Session,
    account_id: str,
    control_id: str,
    new_status: str,
    actor_user_id: str | None = None,
    actor_email: str | None = None,
) -> int:
    """Auto-close open/in_progress remediation tasks when a control is set to Implemented/Partial."""
    tasks = [
        t for t in db.list(RemediationTask, account_id)
        if t.related_control_id == control_id and t.status in ("open", "in_progress")
    ]

    now = datetime.utcnow()
    for task in tasks:
        task.status = "completed"
        task.completed_at = now
        task.closure_note = f"Auto-closed — control status set to '{new_status}'."
        audit_service.emit(
            db, account_id, "remediation.auto_close",
            actor_user_id=actor_user_id,
            actor_email=actor_email,
            entity_type="remediation_task",
            entity_id=task.id,
            entity_label=task.title,
            after_state={"control_id": control_id, "new_status": new_status},
        )
    return len(tasks)


def auto_close_tasks_for_question(
    db: Session,
    account_id: str,
    question_id: str,
    maturity_level: int,
    actor_user_id: str | None = None,
    actor_email: str | None = None,
) -> int:
    """Auto-close open/in_progress remediation tasks when an assessment answer reaches maturity >= 2."""
    tasks = [
        t for t in db.list(RemediationTask, account_id)
        if t.question_id == question_id and t.status in ("open", "in_progress")
    ]

    now = datetime.utcnow()
    for task in tasks:
        task.status = "completed"
        task.completed_at = now
        task.closure_note = f"Auto-closed — assessment maturity raised to level {maturity_level}."
        audit_service.emit(
            db, account_id, "remediation.auto_close",
            actor_user_id=actor_user_id,
            actor_email=actor_email,
            entity_type="remediation_task",
            entity_id=task.id,
            entity_label=task.title,
            after_state={"question_id": question_id, "maturity_level": maturity_level},
        )
    return len(tasks)


# ---------------------------------------------------------------------------
# Plan progress
# ---------------------------------------------------------------------------


def get_plan_progress(plan: RemediationPlan) -> dict:
    """Return milestone and task completion stats for a plan."""
    total_ms = len(plan.milestones)
    done_ms = sum(1 for m in plan.milestones if m.completed_at)
    total_tasks = len(plan.tasks)
    done_tasks = sum(1 for t in plan.tasks if t.status == "completed")

    return {
        "milestone_total": total_ms,
        "milestone_completed": done_ms,
        "milestone_pct": round(done_ms / total_ms * 100) if total_ms > 0 else 0,
        "task_total": total_tasks,
        "task_completed": done_tasks,
        "task_pct": round(done_tasks / total_tasks * 100) if total_tasks > 0 else 0,
    }
