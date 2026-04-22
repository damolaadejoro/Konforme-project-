"""Router for Phase 4: People Tasks — Continuous Compliance."""

import logging
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from auth import enforce_account_access, get_current_account, get_current_user, require_role
from database import get_db
from models import Account, PeopleTask, PeopleTaskCompletion, User, UserRole
import audit_service
import people_tasks_service
from schemas import (
    BaselineInstantiateRequest,
    CompletePeopleTaskRequest,
    CreatePeopleTaskRequest,
    ISMSCoverageResponse,
    MyPeopleTaskItem,
    PeopleTaskCompletionResponse,
    PeopleTaskResponse,
    ReschedulePeopleTaskRequest,
    UpdatePeopleTaskRequest,
)

logger = logging.getLogger(__name__)

router = APIRouter()


def _task_to_response(db: Session, task: PeopleTask, user_id: str | None = None) -> PeopleTaskResponse:
    """Convert a PeopleTask ORM object to PeopleTaskResponse."""
    completion_count = (
        db.query(func.count(PeopleTaskCompletion.id))
        .filter(PeopleTaskCompletion.people_task_id == task.id)
        .scalar()
    ) or 0

    period_status = people_tasks_service.get_task_period_status(db, task, user_id)

    return PeopleTaskResponse(
        id=task.id,
        title=task.title,
        description=task.description,
        taskType=task.task_type,
        pdcaPhase=task.pdca_phase,
        article21Subsection=task.article_21_subsection,
        frequency=task.frequency,
        nextDueDate=task.next_due_date.isoformat() if task.next_due_date else None,
        assigneeUserId=task.assignee_user_id,
        assigneeRole=task.assignee_role,
        relatedControlId=task.related_control_id,
        relatedProcessId=task.related_process_id,
        relatedPlanId=task.related_plan_id,
        requiresEvidence=task.requires_evidence,
        attestationStatement=task.attestation_statement,
        baselineTemplateId=task.baseline_template_id,
        ismsDomain=task.isms_domain,
        active=task.active,
        createdAt=task.created_at.isoformat() if task.created_at else "",
        updatedAt=task.updated_at.isoformat() if task.updated_at else "",
        currentPeriodStatus=period_status,
        completionCount=completion_count,
    )


# --- Baseline templates (read-only, for wizard preview) ---

@router.get("/people-tasks/baseline-templates")
def get_baseline_templates_endpoint(
    _user: User = Depends(get_current_user),
):
    """Return all baseline templates for the wizard preview (no DB writes)."""
    from scripts.seed_continuous_baseline import get_baseline_templates
    templates = get_baseline_templates()
    return [
        {
            "templateId": t["template_id"],
            "title": t["title"],
            "description": t.get("description", ""),
            "taskType": t["task_type"],
            "pdcaPhase": t["pdca_phase"],
            "article21Subsection": t["article_21_subsection"],
            "frequency": t["frequency"],
            "relatedControlId": t.get("related_control_id"),
            "requiresEvidence": t.get("requires_evidence", False),
            "perProcess": t.get("per_process", False),
            "ismsDomain": t.get("isms_domain"),
        }
        for t in templates
    ]


# --- My tasks (must be before /{account_id} to avoid "my" being treated as account_id) ---

@router.get("/people-tasks/my", response_model=list[MyPeopleTaskItem])
def get_my_people_tasks(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get current user's assigned tasks (or all active tasks for the org)."""
    tasks = (
        db.query(PeopleTask)
        .filter(
            PeopleTask.account_id == user.account_id,
            PeopleTask.active.is_(True),
        )
        .order_by(PeopleTask.next_due_date.asc().nullslast())
        .all()
    )

    result = []
    for t in tasks:
        if t.assignee_user_id and t.assignee_user_id != user.id:
            continue
        if t.assignee_role and t.assignee_role != user.role:
            continue

        pk = people_tasks_service.compute_period_key(t.frequency)
        status = people_tasks_service.get_task_period_status(db, t, user.id)

        result.append(MyPeopleTaskItem(
            id=t.id,
            title=t.title,
            description=t.description,
            taskType=t.task_type,
            pdcaPhase=t.pdca_phase,
            article21Subsection=t.article_21_subsection,
            frequency=t.frequency,
            nextDueDate=t.next_due_date.isoformat() if t.next_due_date else None,
            requiresEvidence=t.requires_evidence,
            attestationStatement=t.attestation_statement,
            relatedControlId=t.related_control_id,
            ismsDomain=t.isms_domain,
            currentPeriodKey=pk,
            currentPeriodStatus=status,
        ))

    return result


# --- List tasks ---

@router.get("/people-tasks/{account_id}", response_model=list[PeopleTaskResponse])
def list_people_tasks(
    account_id: str,
    active_only: bool = Query(True),
    pdca_phase: str | None = Query(None),
    subsection: str | None = Query(None),
    task_type: str | None = Query(None),
    isms_domain: str | None = Query(None),
    account: Account = Depends(get_current_account),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    enforce_account_access(account, account_id)
    q = db.query(PeopleTask).filter(PeopleTask.account_id == account_id)
    if active_only:
        q = q.filter(PeopleTask.active.is_(True))
    if pdca_phase:
        q = q.filter(PeopleTask.pdca_phase == pdca_phase)
    if subsection:
        q = q.filter(PeopleTask.article_21_subsection == subsection)
    if task_type:
        q = q.filter(PeopleTask.task_type == task_type)
    if isms_domain:
        q = q.filter(PeopleTask.isms_domain == isms_domain)

    tasks = q.order_by(PeopleTask.next_due_date.asc().nullslast(), PeopleTask.created_at.desc()).all()
    return [_task_to_response(db, t, user.id) for t in tasks]


# --- Create task ---

@router.post("/people-tasks/{account_id}", response_model=PeopleTaskResponse, status_code=201)
def create_people_task(
    account_id: str,
    body: CreatePeopleTaskRequest,
    account: Account = Depends(get_current_account),
    user: User = Depends(require_role(UserRole.owner, UserRole.admin)),
    db: Session = Depends(get_db),
):
    enforce_account_access(account, account_id)

    task = PeopleTask(
        account_id=account_id,
        title=body.title,
        description=body.description,
        task_type=body.task_type,
        pdca_phase=body.pdca_phase,
        article_21_subsection=body.article_21_subsection,
        frequency=body.frequency,
        next_due_date=date.fromisoformat(body.next_due_date) if body.next_due_date else people_tasks_service._compute_initial_due_date(body.frequency),
        assignee_user_id=body.assignee_user_id,
        assignee_role=body.assignee_role,
        related_control_id=body.related_control_id,
        related_process_id=body.related_process_id,
        related_plan_id=body.related_plan_id,
        requires_evidence=body.requires_evidence,
        attestation_statement=body.attestation_statement,
        isms_domain=body.isms_domain,
    )
    db.add(task)

    audit_service.emit(
        db, account_id, "people_tasks.created",
        actor_user_id=user.id,
        entity_type="people_task",
        entity_id=task.id,
        entity_label=task.title,
    )

    db.commit()
    db.refresh(task)
    return _task_to_response(db, task, user.id)


# --- Update task ---

@router.patch("/people-tasks/{account_id}/{task_id}", response_model=PeopleTaskResponse)
def update_people_task(
    account_id: str,
    task_id: str,
    body: UpdatePeopleTaskRequest,
    account: Account = Depends(get_current_account),
    user: User = Depends(require_role(UserRole.owner, UserRole.admin)),
    db: Session = Depends(get_db),
):
    enforce_account_access(account, account_id)
    task = db.query(PeopleTask).filter(PeopleTask.id == task_id, PeopleTask.account_id == account_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    updates = body.model_dump(exclude_unset=True)
    change_reason = updates.pop("change_reason", None)

    # Check if material fields are being changed
    material_changed = bool(people_tasks_service.MATERIAL_FIELDS & set(updates.keys()))
    if material_changed and not change_reason:
        raise HTTPException(status_code=422, detail="change_reason required for material field changes")

    before = {k: getattr(task, k, None) for k in updates}

    for field, value in updates.items():
        if field == "next_due_date" and value:
            setattr(task, field, date.fromisoformat(value))
        else:
            setattr(task, field, value)

    audit_service.emit(
        db, account_id, "people_tasks.updated",
        actor_user_id=user.id,
        entity_type="people_task",
        entity_id=task.id,
        entity_label=task.title,
        before_state=before,
        after_state=updates,
        change_reason=change_reason,
        is_material=material_changed,
    )

    db.commit()
    db.refresh(task)
    return _task_to_response(db, task, user.id)


# --- Reschedule ---

@router.post("/people-tasks/{account_id}/{task_id}/reschedule", response_model=PeopleTaskResponse)
def reschedule_people_task(
    account_id: str,
    task_id: str,
    body: ReschedulePeopleTaskRequest,
    account: Account = Depends(get_current_account),
    user: User = Depends(require_role(UserRole.owner, UserRole.admin)),
    db: Session = Depends(get_db),
):
    enforce_account_access(account, account_id)
    task = db.query(PeopleTask).filter(PeopleTask.id == task_id, PeopleTask.account_id == account_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    old_due = task.next_due_date.isoformat() if task.next_due_date else None
    task.next_due_date = date.fromisoformat(body.new_due_date)

    audit_service.emit(
        db, account_id, "people_tasks.rescheduled",
        actor_user_id=user.id,
        entity_type="people_task",
        entity_id=task.id,
        entity_label=task.title,
        before_state={"next_due_date": old_due},
        after_state={"next_due_date": body.new_due_date},
        change_reason=body.reason,
        is_material=True,
        metadata={"category": body.category},
    )

    db.commit()
    db.refresh(task)
    return _task_to_response(db, task, user.id)


# --- Complete task ---

@router.post("/people-tasks/{account_id}/{task_id}/complete", response_model=PeopleTaskCompletionResponse, status_code=201)
def complete_people_task(
    account_id: str,
    task_id: str,
    body: CompletePeopleTaskRequest,
    account: Account = Depends(get_current_account),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    enforce_account_access(account, account_id)
    task = db.query(PeopleTask).filter(PeopleTask.id == task_id, PeopleTask.account_id == account_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if not task.active:
        raise HTTPException(status_code=400, detail="Task is not active")

    try:
        completion = people_tasks_service.complete_task(
            db, task, user,
            attestation_response=body.attestation_response,
            evidence_id=body.evidence_id,
        )
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))

    db.commit()
    db.refresh(completion)

    return PeopleTaskCompletionResponse(
        id=completion.id,
        peopleTaskId=completion.people_task_id,
        userId=completion.user_id,
        userName=user.name,
        userEmail=user.email,
        periodKey=completion.period_key,
        attestedAt=completion.attested_at.isoformat() if completion.attested_at else None,
        attestationResponse=completion.attestation_response,
        evidenceId=completion.evidence_id,
        createdAt=completion.created_at.isoformat() if completion.created_at else "",
    )


# --- Completion history ---

@router.get("/people-tasks/{account_id}/{task_id}/completions", response_model=list[PeopleTaskCompletionResponse])
def list_task_completions(
    account_id: str,
    task_id: str,
    account: Account = Depends(get_current_account),
    db: Session = Depends(get_db),
):
    enforce_account_access(account, account_id)
    task = db.query(PeopleTask).filter(PeopleTask.id == task_id, PeopleTask.account_id == account_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    completions = (
        db.query(PeopleTaskCompletion)
        .filter(PeopleTaskCompletion.people_task_id == task_id)
        .order_by(PeopleTaskCompletion.created_at.desc())
        .all()
    )

    # Resolve user names
    user_ids = {c.user_id for c in completions}
    users_map = {u.id: u for u in db.query(User).filter(User.id.in_(user_ids)).all()} if user_ids else {}

    return [
        PeopleTaskCompletionResponse(
            id=c.id,
            peopleTaskId=c.people_task_id,
            userId=c.user_id,
            userName=users_map[c.user_id].name if c.user_id in users_map else None,
            userEmail=users_map[c.user_id].email if c.user_id in users_map else None,
            periodKey=c.period_key,
            attestedAt=c.attested_at.isoformat() if c.attested_at else None,
            attestationResponse=c.attestation_response,
            evidenceId=c.evidence_id,
            createdAt=c.created_at.isoformat() if c.created_at else "",
        )
        for c in completions
    ]


# --- ISMS coverage ---

@router.get("/isms/coverage/{account_id}", response_model=ISMSCoverageResponse)
def get_isms_coverage(
    account_id: str,
    account: Account = Depends(get_current_account),
    db: Session = Depends(get_db),
):
    enforce_account_access(account, account_id)
    return people_tasks_service.get_isms_coverage(db, account_id)


# --- Instantiate baseline ---

@router.post("/people-tasks/{account_id}/instantiate-baseline")
def instantiate_baseline(
    account_id: str,
    body: BaselineInstantiateRequest | None = None,
    account: Account = Depends(get_current_account),
    user: User = Depends(require_role(UserRole.owner, UserRole.admin)),
    db: Session = Depends(get_db),
):
    enforce_account_access(account, account_id)

    excluded = set(body.excluded_template_ids) if body and body.excluded_template_ids else None
    assignments = {a.template_id: a for a in (body.assignments or [])} if body else None

    result = people_tasks_service.instantiate_baseline(
        db, account_id,
        actor_user_id=user.id,
        excluded_ids=excluded,
        assignments=assignments,
    )

    # Also consume any pending instantiations from Phase 3
    consumed = people_tasks_service.consume_pending_instantiations(db, account_id)
    result["consumed_pending"] = consumed

    db.commit()
    return result
