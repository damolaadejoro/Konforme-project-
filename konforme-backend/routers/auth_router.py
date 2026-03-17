import threading
import uuid
from datetime import datetime, timedelta, timezone

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy.orm import Session

from audit import log_auth_success, log_login_failure, log_register
from auth import (
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
    get_current_account,
    get_current_user,
    hash_password,
    verify_password,
)
from config import settings
from database import get_db
from email_service import send_password_reset_email, send_verification_email
from models import Account, User, UserRole
from rate_limit import limiter
from schemas import AuthResponse, ForgotPasswordRequest, LoginRequest, RegisterRequest, ResetPasswordRequest

router = APIRouter()

LOCKOUT_THRESHOLD = 5
LOCKOUT_DURATION_MINUTES = 15


def _validate_password(password: str) -> None:
    """Enforce password complexity: min 8 chars, uppercase, lowercase, digit, special char."""
    if len(password) < 8:
        raise HTTPException(status_code=422, detail="Password must be at least 8 characters")
    import re
    if not re.search(r"[A-Z]", password):
        raise HTTPException(status_code=422, detail="Password must contain at least one uppercase letter")
    if not re.search(r"[a-z]", password):
        raise HTTPException(status_code=422, detail="Password must contain at least one lowercase letter")
    if not re.search(r"\d", password):
        raise HTTPException(status_code=422, detail="Password must contain at least one digit")
    if not re.search(r"[^A-Za-z0-9]", password):
        raise HTTPException(status_code=422, detail="Password must contain at least one special character")


def _set_auth_cookies(response: Response, access_token: str, refresh_token: str, csrf_token: str) -> None:
    cookie_kwargs = {
        "httponly": True,
        "secure": settings.cookie_secure,
        "samesite": settings.cookie_samesite,
    }
    if settings.cookie_domain:
        cookie_kwargs["domain"] = settings.cookie_domain

    response.set_cookie(
        key="access_token",
        value=access_token,
        max_age=settings.access_token_expire_minutes * 60,
        path="/",
        **cookie_kwargs,
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        max_age=settings.refresh_token_expire_days * 86400,
        path="/api/v1/auth",
        **cookie_kwargs,
    )
    # CSRF token: NOT httpOnly so JS can read it
    csrf_cookie_kwargs = {
        "httponly": False,
        "secure": settings.cookie_secure,
        "samesite": settings.cookie_samesite,
    }
    if settings.cookie_domain:
        csrf_cookie_kwargs["domain"] = settings.cookie_domain
    response.set_cookie(
        key="csrf_token",
        value=csrf_token,
        max_age=settings.refresh_token_expire_days * 86400,
        path="/",
        **csrf_cookie_kwargs,
    )


def _clear_auth_cookies(response: Response) -> None:
    response.delete_cookie(key="access_token", path="/")
    response.delete_cookie(key="refresh_token", path="/api/v1/auth")
    response.delete_cookie(key="csrf_token", path="/")


def _generate_csrf_token() -> str:
    import secrets
    return secrets.token_urlsafe(32)


def _notify_signup(name: str, email: str, country: str | None):
    """Fire-and-forget POST to webhook URL on new signup."""
    url = settings.signup_webhook_url
    if not url:
        return

    def _send():
        try:
            country_text = country or "Not set"
            ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
            payload = {
                "text": f"New Konforme signup: *{name}* ({email}) — Country: {country_text} — {ts}",
            }
            httpx.post(url, json=payload, timeout=5)
        except Exception:
            pass

    threading.Thread(target=_send, daemon=True).start()


def _send_verification_async(email: str, token: str):
    """Fire-and-forget verification email."""
    def _send():
        try:
            send_verification_email(email, token)
        except Exception:
            pass
    threading.Thread(target=_send, daemon=True).start()


@router.post("/auth/register", response_model=AuthResponse)
@limiter.limit("3/minute")
def register(req: RegisterRequest, request: Request, response: Response, db: Session = Depends(get_db)):
    _validate_password(req.password)

    # Check if email exists in either Account or User
    existing_user = db.query(User).filter(User.email == req.email).first()
    existing_account = db.query(Account).filter(Account.email == req.email).first()
    if existing_user or existing_account:
        raise HTTPException(status_code=409, detail="An account with this email already exists")

    verification_token = str(uuid.uuid4())

    hashed = hash_password(req.password)

    # Create Account (org)
    account = Account(
        name=req.name,
        email=req.email,
        country=req.country,
        language=req.language or "en",
        email_verified=False,
    )
    db.add(account)
    db.flush()

    # Create owner User
    user = User(
        account_id=account.id,
        name=req.name,
        email=req.email,
        password_hash=hashed,
        role=UserRole.owner.value,
        email_verified=False,
        email_verification_token=verification_token,
    )
    db.add(user)
    db.commit()
    db.refresh(account)
    db.refresh(user)

    access_token = create_access_token(account.id, user.id)
    refresh_token = create_refresh_token(account.id, user.id)
    csrf_token = _generate_csrf_token()
    log_register(account.id, account.email)

    _notify_signup(account.name, account.email, account.country)
    _send_verification_async(user.email, verification_token)

    _set_auth_cookies(response, access_token, refresh_token, csrf_token)

    return AuthResponse(
        access_token=access_token,
        account_id=account.id,
        account_name=account.name,
        email=user.email,
        email_verified=user.email_verified,
        country=account.country,
        language=account.language,
        user_id=user.id,
        role=user.role,
    )


@router.post("/auth/login", response_model=AuthResponse)
@limiter.limit("5/minute")
def login(req: LoginRequest, request: Request, response: Response, db: Session = Depends(get_db)):
    # Try User table first, fall back to Account for backward compat
    user = db.query(User).filter(User.email == req.email, User.is_active.is_(True)).first()

    if user:
        # Check user lockout
        if user.locked_until and user.locked_until > datetime.now(timezone.utc):
            remaining = int((user.locked_until - datetime.now(timezone.utc)).total_seconds() / 60) + 1
            raise HTTPException(
                status_code=423,
                detail=f"Account is locked due to too many failed attempts. Try again in {remaining} minutes.",
            )

        if not user.password_hash or not verify_password(req.password, user.password_hash):
            log_login_failure(req.email)
            user.failed_login_attempts = (user.failed_login_attempts or 0) + 1
            if user.failed_login_attempts >= LOCKOUT_THRESHOLD:
                user.locked_until = datetime.now(timezone.utc) + timedelta(minutes=LOCKOUT_DURATION_MINUTES)
            db.commit()
            raise HTTPException(status_code=401, detail="Invalid email or password")

        user.failed_login_attempts = 0
        user.locked_until = None
        db.commit()

        account = user.account
        access_token = create_access_token(account.id, user.id)
        refresh_token = create_refresh_token(account.id, user.id)
        csrf_token = _generate_csrf_token()
        log_auth_success(account.id)

        _set_auth_cookies(response, access_token, refresh_token, csrf_token)

        return AuthResponse(
            access_token=access_token,
            account_id=account.id,
            account_name=account.name,
            email=user.email,
            email_verified=user.email_verified,
            country=account.country,
            language=account.language,
            user_id=user.id,
            role=user.role,
        )

    # No user found
    log_login_failure(req.email)
    raise HTTPException(status_code=401, detail="Invalid email or password")


@router.post("/auth/refresh")
@limiter.limit("10/minute")
def refresh(request: Request, response: Response, db: Session = Depends(get_db)):
    token = request.cookies.get("refresh_token")
    if not token:
        raise HTTPException(status_code=401, detail="No refresh token")

    token_data = decode_refresh_token(token)
    account_id = token_data["account_id"]
    user_id = token_data.get("user_id")

    account = db.query(Account).filter(
        Account.id == account_id,
        Account.is_active.is_(True),
    ).first()
    if not account:
        raise HTTPException(status_code=401, detail="Account not found or inactive")

    user = None
    if user_id:
        user = db.query(User).filter(User.id == user_id, User.is_active.is_(True)).first()

    access_token = create_access_token(account.id, user.id if user else None)
    refresh_token = create_refresh_token(account.id, user.id if user else None)
    csrf_token = _generate_csrf_token()

    _set_auth_cookies(response, access_token, refresh_token, csrf_token)

    result = {
        "account_id": account.id,
        "account_name": account.name,
        "email": user.email if user else account.email,
        "email_verified": user.email_verified if user else account.email_verified,
        "country": account.country,
        "language": account.language,
    }
    if user:
        result["user_id"] = user.id
        result["role"] = user.role
    return result


@router.post("/auth/logout")
def logout(response: Response):
    _clear_auth_cookies(response)
    return {"detail": "Logged out"}


@router.get("/auth/me")
@limiter.limit("30/minute")
def get_me(request: Request, db: Session = Depends(get_db), account: Account = Depends(get_current_account)):
    # Try to find the User for richer response
    user = None
    try:
        from auth import get_current_user as _get_user, bearer_scheme as _bs, _extract_token
        token = _extract_token(request, None)
        if not token:
            creds = request.headers.get("authorization")
            if creds and creds.startswith("Bearer "):
                token = creds[7:]
        if token:
            from auth import decode_access_token
            token_data = decode_access_token(token)
            uid = token_data.get("user_id")
            if uid:
                user = db.query(User).filter(User.id == uid, User.is_active.is_(True)).first()
    except Exception:
        pass

    if not user:
        # Fallback: find first user for this account
        user = db.query(User).filter(User.account_id == account.id, User.is_active.is_(True)).order_by(User.created_at).first()

    result = {
        "account_id": account.id,
        "account_name": account.name,
        "email": user.email if user else account.email,
        "email_verified": user.email_verified if user else account.email_verified,
        "country": account.country,
        "language": account.language,
    }
    if user:
        result["user_id"] = user.id
        result["role"] = user.role
    return result


@router.post("/auth/verify-email")
def verify_email(token: str, db: Session = Depends(get_db)):
    """Public endpoint — verifies email by token."""
    user = db.query(User).filter(User.email_verification_token == token).first()
    if not user:
        raise HTTPException(status_code=400, detail="Invalid or expired verification token")

    user.email_verified = True
    user.email_verification_token = None
    # Also update Account-level flag
    account = user.account
    if account:
        account.email_verified = True
    db.commit()
    return {"detail": "Email verified successfully"}


@router.post("/auth/resend-verification")
@limiter.limit("3/minute")
def resend_verification(request: Request, account: Account = Depends(get_current_account), db: Session = Depends(get_db)):
    """Resend verification email for the authenticated user."""
    user = db.query(User).filter(User.account_id == account.id, User.is_active.is_(True)).order_by(User.created_at).first()

    if user and user.email_verified:
        return {"detail": "Email is already verified"}

    if not user:
        return {"detail": "No user found"}

    verification_token = str(uuid.uuid4())
    user.email_verification_token = verification_token
    db.commit()

    _send_verification_async(user.email, verification_token)

    return {"detail": "Verification email sent"}


@router.post("/auth/forgot-password")
@limiter.limit("3/minute")
def forgot_password(req: ForgotPasswordRequest, request: Request, db: Session = Depends(get_db)):
    """Step 1: Send a password reset email with a secure token."""
    import secrets

    # Always return the same response to prevent email enumeration
    generic_response = {"detail": "If an account with that email exists, a reset link has been sent."}

    user = db.query(User).filter(User.email == req.email, User.is_active.is_(True)).first()
    if not user:
        return generic_response

    # Generate a secure, time-limited token
    token = secrets.token_urlsafe(32)
    user.password_reset_token = token
    user.password_reset_expires = datetime.now(timezone.utc) + timedelta(hours=1)
    db.commit()

    # Fire-and-forget email
    def _send():
        try:
            send_password_reset_email(user.email, token)
        except Exception:
            pass
    threading.Thread(target=_send, daemon=True).start()

    return generic_response


@router.post("/auth/reset-password")
@limiter.limit("5/minute")
def reset_password(req: ResetPasswordRequest, request: Request, db: Session = Depends(get_db)):
    """Step 2: Reset password using a valid token from the email."""
    _validate_password(req.new_password)

    user = db.query(User).filter(
        User.password_reset_token == req.token,
        User.is_active.is_(True),
    ).first()

    if not user or not user.password_reset_expires:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")

    if user.password_reset_expires < datetime.now(timezone.utc):
        # Token expired — clear it
        user.password_reset_token = None
        user.password_reset_expires = None
        db.commit()
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")

    new_hash = hash_password(req.new_password)
    user.password_hash = new_hash
    user.failed_login_attempts = 0
    user.locked_until = None
    user.password_reset_token = None
    user.password_reset_expires = None
    db.commit()

    return {"detail": "Password has been reset successfully. You can now sign in."}
