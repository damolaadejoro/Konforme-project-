"""CRUD endpoints for per-account control state and employee campaigns."""

import secrets
from datetime import date, datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from auth import enforce_account_access, get_current_account
from config import settings
from database import get_db
from email_service import send_campaign_task_email
from models import Account, AccountControl, BaseControl, CampaignTask, ControlCampaign
from rate_limit import limiter
from schemas import (
    AccountControlBulkRequest,
    AccountControlResponse,
    AccountControlUpdate,
    BaseControlResponse,
    CampaignResponse,
    CampaignTaskResponse,
    CampaignTaskUpdate,
    CreateCampaignRequest,
)

router = APIRouter()


def _ctrl_to_response(ac: AccountControl) -> AccountControlResponse:
    return AccountControlResponse(
        id=ac.id,
        controlId=ac.control_id,
        status=ac.status,
        owner=ac.owner,
        dueDate=ac.due_date.isoformat() if ac.due_date else None,
        notes=ac.notes,
        isCountrySpecific=ac.is_country_specific,
        lastUpdated=ac.last_updated.isoformat() if ac.last_updated else "",
    )


def _task_to_response(t: CampaignTask) -> CampaignTaskResponse:
    return CampaignTaskResponse(
        id=t.id,
        controlId=t.control_id,
        campaignId=t.campaign_id,
        employeeName=t.employee_name,
        employeeEmail=t.employee_email,
        department=t.department,
        taskType=t.task_type,
        status=t.status,
        sentDate=t.sent_date.isoformat() if t.sent_date else "",
        completedDate=t.completed_date.isoformat() if t.completed_date else None,
        deadline=t.deadline,
        score=t.score,
    )


def _campaign_to_response(c: ControlCampaign) -> CampaignResponse:
    return CampaignResponse(
        id=c.id,
        controlId=c.control_id,
        controlName=c.control_name,
        taskType=c.task_type,
        deadline=c.deadline,
        createdAt=c.created_at.isoformat() if c.created_at else "",
        policyContent=c.policy_content,
        tasks=[_task_to_response(t) for t in c.tasks],
    )


# ---------------------------------------------------------------------------
# Base Controls (public — control definitions, not per-account state)
# ---------------------------------------------------------------------------


@router.get("/base-controls", response_model=list[BaseControlResponse])
def list_base_controls(db: Session = Depends(get_db)):
    """Return all 43 NIS2 control definitions. No auth required."""
    rows = db.query(BaseControl).order_by(BaseControl.display_order).all()
    return [
        BaseControlResponse(
            controlId=c.control_id,
            title=c.title,
            description=c.description,
            article=c.article,
            articleArea=c.article_area,
            category=c.category,
            severity=c.severity,
            isPeopleControl=c.is_people_control,
        )
        for c in rows
    ]


# ---------------------------------------------------------------------------
# Controls
# ---------------------------------------------------------------------------


@router.get("/controls/{account_id}", response_model=list[AccountControlResponse])
def list_controls(
    account_id: str,
    account: Account = Depends(get_current_account),
    db: Session = Depends(get_db),
):
    enforce_account_access(account, account_id)
    rows = (
        db.query(AccountControl)
        .filter(AccountControl.account_id == account_id)
        .order_by(AccountControl.control_id)
        .all()
    )
    return [_ctrl_to_response(r) for r in rows]


@router.put("/controls/{account_id}/bulk", response_model=list[AccountControlResponse])
def bulk_upsert_controls(
    account_id: str,
    req: AccountControlBulkRequest,
    account: Account = Depends(get_current_account),
    db: Session = Depends(get_db),
):
    enforce_account_access(account, account_id)

    existing = {
        ac.control_id: ac
        for ac in db.query(AccountControl)
        .filter(AccountControl.account_id == account_id)
        .all()
    }

    import evidence_service

    for item in req.controls:
        # Enforce evidence requirement for Implemented/Partial
        if item.status in ("Implemented", "Partial"):
            linked = evidence_service.get_for_entity(db, account_id, "control", item.control_id)
            if not linked:
                raise HTTPException(
                    status_code=422,
                    detail=f"Control '{item.control_id}': at least one evidence file must be linked before setting status to '{item.status}'.",
                )

        parsed_date = None
        if item.due_date:
            try:
                parsed_date = date.fromisoformat(item.due_date)
            except ValueError:
                pass

        if item.control_id in existing:
            # Only update if the incoming data has meaningful changes
            # (skip if it's just a default seed with "Not Started")
            ac = existing[item.control_id]
            if item.status != "Not Started" or ac.status == "Not Started":
                ac.status = item.status
            if item.owner:
                ac.owner = item.owner
            if parsed_date:
                ac.due_date = parsed_date
            if item.notes:
                ac.notes = item.notes
            ac.is_country_specific = item.is_country_specific
        else:
            ac = AccountControl(
                account_id=account_id,
                control_id=item.control_id,
                status=item.status,
                owner=item.owner,
                due_date=parsed_date,
                notes=item.notes,
                is_country_specific=item.is_country_specific,
            )
            db.add(ac)

    db.commit()

    rows = (
        db.query(AccountControl)
        .filter(AccountControl.account_id == account_id)
        .order_by(AccountControl.control_id)
        .all()
    )
    return [_ctrl_to_response(r) for r in rows]


@router.patch("/controls/{account_id}/{control_id}", response_model=AccountControlResponse)
def update_control(
    account_id: str,
    control_id: str,
    req: AccountControlUpdate,
    account: Account = Depends(get_current_account),
    db: Session = Depends(get_db),
):
    enforce_account_access(account, account_id)

    ac = (
        db.query(AccountControl)
        .filter(
            AccountControl.account_id == account_id,
            AccountControl.control_id == control_id,
        )
        .first()
    )

    if not ac:
        # Auto-create on first PATCH (like assessment auto-save)
        ac = AccountControl(account_id=account_id, control_id=control_id)
        db.add(ac)

    old_status = ac.status
    if req.status is not None:
        # Enforce evidence requirement for Implemented/Partial
        if req.status in ("Implemented", "Partial"):
            import evidence_service
            linked = evidence_service.get_for_entity(db, account_id, "control", control_id)
            if not linked:
                raise HTTPException(
                    status_code=422,
                    detail=f"At least one evidence file must be linked before setting status to '{req.status}'.",
                )
        ac.status = req.status
    if req.owner is not None:
        ac.owner = req.owner
    if req.due_date is not None:
        try:
            ac.due_date = date.fromisoformat(req.due_date) if req.due_date else None
        except ValueError:
            ac.due_date = None
    if req.notes is not None:
        ac.notes = req.notes

    db.commit()
    db.refresh(ac)

    # Auto-manage remediation tasks based on control status changes
    if req.status is not None and old_status != req.status:
        import logging
        import remediation_service
        logger = logging.getLogger(__name__)
        try:
            if req.status in ("Planned", "Not Started"):
                task = remediation_service.auto_create_task_for_control(
                    db, account_id, ac.control_id, ac.status,
                )
                if task:
                    db.commit()
                    logger.info("Auto-created remediation task for control %s", ac.control_id)
            elif req.status in ("Implemented", "Partial"):
                closed = remediation_service.auto_close_tasks_for_control(
                    db, account_id, ac.control_id, ac.status,
                )
                if closed:
                    db.commit()
                    logger.info("Auto-closed %d remediation task(s) for control %s", closed, ac.control_id)
        except Exception as e:
            logger.error("Auto-manage task for control failed: %s", e, exc_info=True)
            db.rollback()

    return _ctrl_to_response(ac)


# ---------------------------------------------------------------------------
# Campaigns
# ---------------------------------------------------------------------------


@router.get("/campaigns/{account_id}", response_model=list[CampaignResponse])
def list_campaigns(
    account_id: str,
    account: Account = Depends(get_current_account),
    db: Session = Depends(get_db),
):
    enforce_account_access(account, account_id)
    rows = (
        db.query(ControlCampaign)
        .filter(ControlCampaign.account_id == account_id)
        .order_by(ControlCampaign.created_at.desc())
        .all()
    )
    return [_campaign_to_response(c) for c in rows]


@router.post("/campaigns/{account_id}", response_model=CampaignResponse, status_code=201)
def create_campaign(
    account_id: str,
    req: CreateCampaignRequest,
    account: Account = Depends(get_current_account),
    db: Session = Depends(get_db),
):
    enforce_account_access(account, account_id)

    campaign = ControlCampaign(
        account_id=account_id,
        control_id=req.control_id,
        control_name=req.control_name,
        task_type=req.task_type,
        deadline=req.deadline,
        policy_content=req.policy_content,
    )
    db.add(campaign)
    db.flush()

    base_url = settings.frontend_base_url

    for emp in req.employees:
        completion_token = secrets.token_urlsafe(32)
        task = CampaignTask(
            campaign_id=campaign.id,
            control_id=req.control_id,
            employee_name=emp.employee_name,
            employee_email=emp.employee_email,
            department=emp.department,
            task_type=req.task_type,
            deadline=req.deadline,
            completion_token=completion_token,
        )
        db.add(task)
        db.flush()

        # Send task email (best-effort)
        completion_url = f"{base_url}/task/complete/{completion_token}"
        task_desc = f"{req.task_type}: {req.control_name}"
        try:
            send_campaign_task_email(
                email=emp.employee_email,
                employee_name=emp.employee_name,
                task_description=task_desc,
                completion_url=completion_url,
                deadline=req.deadline,
                lang=account.language or "en",
            )
        except Exception:
            pass  # non-critical

    db.commit()
    db.refresh(campaign)
    return _campaign_to_response(campaign)


@router.patch("/campaigns/{account_id}/tasks/{task_id}", response_model=CampaignTaskResponse)
def update_campaign_task(
    account_id: str,
    task_id: str,
    req: CampaignTaskUpdate,
    account: Account = Depends(get_current_account),
    db: Session = Depends(get_db),
):
    enforce_account_access(account, account_id)

    task = db.query(CampaignTask).filter(CampaignTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    # Verify the task belongs to this account
    campaign = db.query(ControlCampaign).filter(ControlCampaign.id == task.campaign_id).first()
    if not campaign or campaign.account_id != account_id:
        raise HTTPException(status_code=404, detail="Task not found")

    if req.status is not None:
        task.status = req.status
        if req.status == "completed":
            task.completed_date = datetime.now(timezone.utc)
    if req.score is not None:
        task.score = req.score

    db.commit()
    db.refresh(task)
    return _task_to_response(task)


# ---------------------------------------------------------------------------
# Public task completion (no auth required)
# ---------------------------------------------------------------------------


@router.post("/campaigns/tasks/complete/{token}")
@limiter.limit("10/minute")
def complete_task_by_token(token: str, request: Request, db: Session = Depends(get_db)):
    """Public endpoint — mark a campaign task as completed via unique token."""
    task = db.query(CampaignTask).filter(CampaignTask.completion_token == token).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found or already completed")

    if task.status == "completed":
        return {"detail": "Task already completed", "task_id": task.id}

    task.status = "completed"
    task.completed_date = datetime.now(timezone.utc)
    task.completion_token = None  # Invalidate token after use
    db.commit()

    return {"detail": "Task completed successfully", "task_id": task.id}


@router.get("/campaigns/tasks/complete/{token}")
def get_task_by_token(token: str, db: Session = Depends(get_db)):
    """Public endpoint — get task info for the completion page."""
    task = db.query(CampaignTask).filter(CampaignTask.completion_token == token).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found or already completed")

    campaign = db.query(ControlCampaign).filter(ControlCampaign.id == task.campaign_id).first()

    return {
        "task_id": task.id,
        "employee_name": task.employee_name,
        "task_type": task.task_type,
        "control_name": campaign.control_name if campaign else "",
        "deadline": task.deadline,
        "status": task.status,
        "policy_content": campaign.policy_content if campaign else None,
    }
