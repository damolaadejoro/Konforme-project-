"""CRUD endpoints for business processes and process-control linking (Scoping / SoA)."""

from fastapi import APIRouter, Depends, HTTPException

from auth import enforce_account_access, get_current_account
from database import Session, get_db
from models import Account, BaseControl, BusinessProcess, PeopleTask, ProcessControl
from store import order_by
from schemas import (
    BusinessProcessResponse,
    CreateBusinessProcessRequest,
    LinkControlsRequest,
    ProcessControlResponse,
    SoAEntry,
    UpdateBusinessProcessRequest,
)

router = APIRouter()


def _pc_to_response(pc: ProcessControl) -> ProcessControlResponse:
    return ProcessControlResponse(
        id=pc.id,
        controlId=pc.control_id,
        applicable=pc.applicable,
        justification=pc.justification,
        createdAt=pc.created_at.isoformat() if pc.created_at else "",
    )


def _bp_to_response(bp: BusinessProcess) -> BusinessProcessResponse:
    return BusinessProcessResponse(
        id=bp.id,
        name=bp.name,
        description=bp.description,
        isCritical=bp.is_critical,
        owner=bp.owner,
        createdAt=bp.created_at.isoformat() if bp.created_at else "",
        updatedAt=bp.updated_at.isoformat() if bp.updated_at else "",
        controls=[_pc_to_response(pc) for pc in bp.process_controls],
    )


# ---------------------------------------------------------------------------
# Business Process CRUD
# ---------------------------------------------------------------------------


@router.get("/business-processes/{account_id}", response_model=list[BusinessProcessResponse])
def list_business_processes(
    account_id: str,
    account: Account = Depends(get_current_account),
    db: Session = Depends(get_db),
):
    enforce_account_access(account, account_id)
    rows = order_by(db.list(BusinessProcess, account_id), "created_at")
    return [_bp_to_response(bp) for bp in rows]


# ---------------------------------------------------------------------------
# Statement of Applicability (SoA) — defined before {process_id} routes to avoid path conflict
# ---------------------------------------------------------------------------


@router.get("/business-processes/{account_id}/soa", response_model=list[SoAEntry])
def get_statement_of_applicability(
    account_id: str,
    account: Account = Depends(get_current_account),
    db: Session = Depends(get_db),
):
    """Generate a Statement of Applicability across all business processes."""
    enforce_account_access(account, account_id)

    # Get all base controls
    base_controls = order_by(db.all(BaseControl), "display_order")
    ctrl_map = {bc.control_id: bc for bc in base_controls}

    # Get all process-control links for this account
    processes = order_by(db.list(BusinessProcess, account_id), "created_at")

    # Build per-control aggregation
    soa: dict[str, SoAEntry] = {}
    for bp in processes:
        for pc in bp.process_controls:
            if pc.control_id not in soa:
                bc = ctrl_map.get(pc.control_id)
                soa[pc.control_id] = SoAEntry(
                    controlId=pc.control_id,
                    controlTitle=bc.title if bc else pc.control_id,
                    applicable=pc.applicable,
                    justification=pc.justification,
                    linkedProcesses=[],
                )
            entry = soa[pc.control_id]
            entry.linkedProcesses.append(bp.name)
            # If any process marks the control as applicable, it's applicable overall
            if pc.applicable:
                entry.applicable = True

    # Add controls not linked to any process (show as not-applicable by default)
    for ctrl_id, bc in ctrl_map.items():
        if ctrl_id not in soa:
            soa[ctrl_id] = SoAEntry(
                controlId=ctrl_id,
                controlTitle=bc.title,
                applicable=False,
                justification="",
                linkedProcesses=[],
            )

    return list(soa.values())


@router.post("/business-processes/{account_id}", response_model=BusinessProcessResponse, status_code=201)
def create_business_process(
    account_id: str,
    req: CreateBusinessProcessRequest,
    account: Account = Depends(get_current_account),
    db: Session = Depends(get_db),
):
    enforce_account_access(account, account_id)

    bp = BusinessProcess(
        account_id=account_id,
        name=req.name,
        description=req.description,
        is_critical=req.is_critical,
        owner=req.owner,
    )
    db.add(bp)
    db.commit()
    db.refresh(bp)
    return _bp_to_response(bp)


@router.get("/business-processes/{account_id}/{process_id}", response_model=BusinessProcessResponse)
def get_business_process(
    account_id: str,
    process_id: str,
    account: Account = Depends(get_current_account),
    db: Session = Depends(get_db),
):
    enforce_account_access(account, account_id)

    bp = db.get_by_key(BusinessProcess, account_id, id=process_id)
    if not bp:
        raise HTTPException(status_code=404, detail="Business process not found")
    return _bp_to_response(bp)


@router.patch("/business-processes/{account_id}/{process_id}", response_model=BusinessProcessResponse)
def update_business_process(
    account_id: str,
    process_id: str,
    req: UpdateBusinessProcessRequest,
    account: Account = Depends(get_current_account),
    db: Session = Depends(get_db),
):
    enforce_account_access(account, account_id)

    bp = db.get_by_key(BusinessProcess, account_id, id=process_id)
    if not bp:
        raise HTTPException(status_code=404, detail="Business process not found")

    if req.name is not None:
        bp.name = req.name
    if req.description is not None:
        bp.description = req.description
    if req.is_critical is not None:
        bp.is_critical = req.is_critical
    if req.owner is not None:
        bp.owner = req.owner

    db.commit()
    db.refresh(bp)
    return _bp_to_response(bp)


@router.delete("/business-processes/{account_id}/{process_id}", status_code=204)
def delete_business_process(
    account_id: str,
    process_id: str,
    account: Account = Depends(get_current_account),
    db: Session = Depends(get_db),
):
    enforce_account_access(account, account_id)

    bp = db.get_by_key(BusinessProcess, account_id, id=process_id)
    if not bp:
        raise HTTPException(status_code=404, detail="Business process not found")

    # people_tasks.related_process_id was ON DELETE SET NULL
    for task in db.list(PeopleTask, account_id):
        if task.related_process_id == process_id:
            task.related_process_id = None
    db.delete(bp)
    db.commit()


# ---------------------------------------------------------------------------
# Process ↔ Control Linking
# ---------------------------------------------------------------------------


@router.put(
    "/business-processes/{account_id}/{process_id}/controls",
    response_model=list[ProcessControlResponse],
)
def link_controls(
    account_id: str,
    process_id: str,
    req: LinkControlsRequest,
    account: Account = Depends(get_current_account),
    db: Session = Depends(get_db),
):
    """Replace the control links for a business process (idempotent PUT)."""
    enforce_account_access(account, account_id)

    bp = db.get_by_key(BusinessProcess, account_id, id=process_id)
    if not bp:
        raise HTTPException(status_code=404, detail="Business process not found")

    # Delete existing links and replace
    for old in db.list(ProcessControl, process_id):
        db.delete(old)

    new_links = []
    for item in req.controls:
        pc = ProcessControl(
            business_process_id=process_id,
            control_id=item.control_id,
            applicable=item.applicable,
            justification=item.justification,
        )
        db.add(pc)
        new_links.append(pc)

    db.commit()
    return [_pc_to_response(pc) for pc in new_links]


