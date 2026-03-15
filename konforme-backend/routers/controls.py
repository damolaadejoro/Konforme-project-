"""CRUD endpoints for per-account control state and employee campaigns."""

from datetime import date, datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from auth import enforce_account_access, get_current_account
from database import get_db
from models import Account, AccountControl, CampaignTask, ControlCampaign
from schemas import (
    AccountControlBulkRequest,
    AccountControlResponse,
    AccountControlUpdate,
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

    for item in req.controls:
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

    if req.status is not None:
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

    for emp in req.employees:
        task = CampaignTask(
            campaign_id=campaign.id,
            control_id=req.control_id,
            employee_name=emp.employee_name,
            employee_email=emp.employee_email,
            department=emp.department,
            task_type=req.task_type,
            deadline=req.deadline,
        )
        db.add(task)

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
