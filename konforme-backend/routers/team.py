"""Team management endpoints — invite members, manage roles."""

import secrets
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from auth import get_current_user, hash_password, require_role
from database import get_db
from email_service import send_invite_email
from models import User, UserRole
from rate_limit import limiter
from routers.auth_router import _validate_password
from schemas import AcceptInviteRequest, InviteRequest, TeamMemberResponse, UpdateMemberRoleRequest

INVITE_TOKEN_EXPIRY_DAYS = 7

router = APIRouter()


def _user_to_response(u: User) -> TeamMemberResponse:
    return TeamMemberResponse(
        id=u.id,
        name=u.name,
        email=u.email,
        role=u.role,
        emailVerified=u.email_verified,
        isActive=u.is_active,
        inviteAccepted=u.invite_accepted_at is not None or u.role == UserRole.owner.value,
        createdAt=u.created_at.isoformat() if u.created_at else "",
    )


@router.get("/team/members", response_model=list[TeamMemberResponse])
def list_members(
    user: User = Depends(require_role(UserRole.owner, UserRole.admin)),
    db: Session = Depends(get_db),
):
    members = (
        db.query(User)
        .filter(User.account_id == user.account_id)
        .order_by(User.created_at)
        .all()
    )
    return [_user_to_response(m) for m in members]


@router.post("/team/invite", response_model=list[TeamMemberResponse], status_code=201)
def invite_members(
    req: InviteRequest,
    user: User = Depends(require_role(UserRole.owner, UserRole.admin)),
    db: Session = Depends(get_db),
):
    if req.role not in ("admin", "member"):
        raise HTTPException(status_code=422, detail="Role must be 'admin' or 'member'")

    invited = []
    for email in req.emails:
        email_lower = email.lower().strip()

        # Check if user already exists in this account
        existing = db.query(User).filter(User.email == email_lower).first()
        if existing:
            if existing.account_id == user.account_id:
                continue  # Already a member, skip
            raise HTTPException(
                status_code=409,
                detail=f"Email {email_lower} is already associated with another organization",
            )

        invite_token = secrets.token_urlsafe(32)
        new_user = User(
            account_id=user.account_id,
            name=email_lower.split("@")[0],  # placeholder name
            email=email_lower,
            role=req.role,
            invite_token=invite_token,
            invite_expires=datetime.now(timezone.utc) + timedelta(days=INVITE_TOKEN_EXPIRY_DAYS),
            is_active=False,  # Activated on invite acceptance
            email_verified=False,
        )
        db.add(new_user)
        db.flush()

        # Send invite email (fire-and-forget)
        account = user.account
        try:
            send_invite_email(
                email=email_lower,
                inviter_name=user.name,
                org_name=account.name,
                token=invite_token,
                lang=account.language or "en",
            )
        except Exception:
            pass  # non-critical

        invited.append(new_user)

    db.commit()
    return [_user_to_response(u) for u in invited]


@router.get("/team/accept-invite")
@limiter.limit("10/hour")
def accept_invite_redirect(token: str, request: Request, db: Session = Depends(get_db)):
    """Public endpoint — validates token and returns info for the frontend signup form."""
    user = db.query(User).filter(User.invite_token == token).first()
    if not user:
        raise HTTPException(status_code=400, detail="Invalid or expired invitation token")

    # Check token expiry
    if user.invite_expires and (user.invite_expires.replace(tzinfo=timezone.utc) if user.invite_expires.tzinfo is None else user.invite_expires) < datetime.now(timezone.utc):
        user.invite_token = None
        user.invite_expires = None
        db.commit()
        raise HTTPException(status_code=400, detail="Invalid or expired invitation token")

    account = user.account
    return {
        "email": user.email,
        "org_name": account.name if account else "",
        "token": token,
    }


@router.post("/team/accept-invite")
@limiter.limit("10/hour")
def accept_invite(req: AcceptInviteRequest, request: Request, db: Session = Depends(get_db)):
    """Public endpoint — accept an invitation by setting name and password."""
    _validate_password(req.password)

    user = db.query(User).filter(User.invite_token == req.token).first()
    if not user:
        raise HTTPException(status_code=400, detail="Invalid or expired invitation token")

    if user.invite_accepted_at:
        raise HTTPException(status_code=400, detail="Invitation has already been accepted")

    # Check token expiry
    if user.invite_expires and (user.invite_expires.replace(tzinfo=timezone.utc) if user.invite_expires.tzinfo is None else user.invite_expires) < datetime.now(timezone.utc):
        user.invite_token = None
        user.invite_expires = None
        db.commit()
        raise HTTPException(status_code=400, detail="Invalid or expired invitation token")

    user.name = req.name
    user.password_hash = hash_password(req.password)
    user.invite_token = None
    user.invite_expires = None
    user.invite_accepted_at = datetime.now(timezone.utc)
    user.email_verified = True  # Verified by accepting invite link
    user.is_active = True  # Activate user on acceptance
    db.commit()

    return {"detail": "Invitation accepted successfully", "email": user.email}


@router.put("/team/members/{user_id}/role", response_model=TeamMemberResponse)
def update_member_role(
    user_id: str,
    req: UpdateMemberRoleRequest,
    user: User = Depends(require_role(UserRole.owner)),
    db: Session = Depends(get_db),
):
    if req.role not in ("admin", "member"):
        raise HTTPException(status_code=422, detail="Role must be 'admin' or 'member'")

    target = db.query(User).filter(User.id == user_id, User.account_id == user.account_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="Member not found")

    if target.role == UserRole.owner.value:
        raise HTTPException(status_code=400, detail="Cannot change the owner's role")

    target.role = req.role
    db.commit()
    db.refresh(target)
    return _user_to_response(target)


@router.delete("/team/members/{user_id}", status_code=204)
def remove_member(
    user_id: str,
    user: User = Depends(require_role(UserRole.owner, UserRole.admin)),
    db: Session = Depends(get_db),
):
    target = db.query(User).filter(User.id == user_id, User.account_id == user.account_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="Member not found")

    if target.id == user.id:
        raise HTTPException(status_code=400, detail="Cannot remove yourself")

    if target.role == UserRole.owner.value:
        # Ensure at least one active owner remains
        owner_count = db.query(User).filter(
            User.account_id == user.account_id,
            User.role == UserRole.owner.value,
            User.is_active.is_(True),
        ).count()
        if owner_count <= 1:
            raise HTTPException(status_code=400, detail="Cannot remove the last account owner")

    target.is_active = False
    db.commit()
