from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from assessment_questions import QUESTION_IDS
from auth import enforce_account_access, get_current_account
from database import get_db
from models import Account, RemediationTask
from schemas import RemediationTaskCreate, RemediationTaskResponse, RemediationTaskUpdate

router = APIRouter()


def _task_to_response(t: RemediationTask) -> RemediationTaskResponse:
    return RemediationTaskResponse(
        id=t.id,
        questionId=t.question_id,
        title=t.title,
        description=t.description,
        status=t.status,
        priority=t.priority,
        assignedTo=t.assigned_to,
        dueDate=t.due_date.isoformat() if t.due_date else None,
        createdAt=t.created_at.isoformat(),
        updatedAt=t.updated_at.isoformat(),
        completedAt=t.completed_at.isoformat() if t.completed_at else None,
    )


@router.post("/remediation/{account_id}", response_model=RemediationTaskResponse)
def create_remediation_task(
    account_id: str,
    req: RemediationTaskCreate,
    account: Account = Depends(get_current_account),
    db: Session = Depends(get_db),
):
    enforce_account_access(account, account_id)

    if req.question_id not in QUESTION_IDS:
        raise HTTPException(status_code=404, detail=f"Unknown question: {req.question_id}")

    from datetime import date
    due = date.fromisoformat(req.due_date) if req.due_date else None

    task = RemediationTask(
        account_id=account_id,
        question_id=req.question_id,
        title=req.title,
        description=req.description,
        priority=req.priority,
        assigned_to=req.assigned_to,
        due_date=due,
    )
    db.add(task)
    db.commit()
    db.refresh(task)

    return _task_to_response(task)


@router.get("/remediation/{account_id}", response_model=list[RemediationTaskResponse])
def list_remediation_tasks(
    account_id: str,
    account: Account = Depends(get_current_account),
    db: Session = Depends(get_db),
):
    enforce_account_access(account, account_id)

    tasks = (
        db.query(RemediationTask)
        .filter(RemediationTask.account_id == account_id)
        .order_by(RemediationTask.created_at.desc())
        .all()
    )

    return [_task_to_response(t) for t in tasks]


@router.patch("/remediation/{account_id}/{task_id}", response_model=RemediationTaskResponse)
def update_remediation_task(
    account_id: str,
    task_id: str,
    req: RemediationTaskUpdate,
    account: Account = Depends(get_current_account),
    db: Session = Depends(get_db),
):
    enforce_account_access(account, account_id)

    task = (
        db.query(RemediationTask)
        .filter(RemediationTask.id == task_id, RemediationTask.account_id == account_id)
        .first()
    )
    if not task:
        raise HTTPException(status_code=404, detail="Remediation task not found")

    if req.title is not None:
        task.title = req.title
    if req.description is not None:
        task.description = req.description
    if req.status is not None:
        task.status = req.status
        if req.status == "completed":
            task.completed_at = datetime.now(timezone.utc)
    if req.priority is not None:
        task.priority = req.priority
    if req.assigned_to is not None:
        task.assigned_to = req.assigned_to
    if req.due_date is not None:
        from datetime import date
        task.due_date = date.fromisoformat(req.due_date)

    db.commit()
    db.refresh(task)

    return _task_to_response(task)
