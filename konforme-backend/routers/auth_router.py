from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy.orm import Session

from audit import log_auth_success, log_login_failure, log_register
from auth import (
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
    get_current_account,
    hash_password,
    verify_password,
)
from config import settings
from database import get_db
from models import Account
from rate_limit import limiter
from schemas import AuthResponse, LoginRequest, RegisterRequest, ResetPasswordRequest

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


@router.post("/auth/register", response_model=AuthResponse)
@limiter.limit("3/minute")
def register(req: RegisterRequest, request: Request, response: Response, db: Session = Depends(get_db)):
    _validate_password(req.password)

    existing = db.query(Account).filter(Account.email == req.email).first()
    if existing:
        raise HTTPException(status_code=409, detail="An account with this email already exists")

    account = Account(
        name=req.name,
        email=req.email,
        password_hash=hash_password(req.password),
        country=req.country,
        language=req.language or "en",
    )
    db.add(account)
    db.commit()
    db.refresh(account)

    access_token = create_access_token(account.id)
    refresh_token = create_refresh_token(account.id)
    csrf_token = _generate_csrf_token()
    log_register(account.id, account.email)

    _set_auth_cookies(response, access_token, refresh_token, csrf_token)

    return AuthResponse(
        access_token=access_token,
        account_id=account.id,
        account_name=account.name,
        email=account.email,
        country=account.country,
        language=account.language,
    )


@router.post("/auth/login", response_model=AuthResponse)
@limiter.limit("5/minute")
def login(req: LoginRequest, request: Request, response: Response, db: Session = Depends(get_db)):
    account = db.query(Account).filter(Account.email == req.email, Account.is_active.is_(True)).first()

    if not account:
        log_login_failure(req.email)
        raise HTTPException(status_code=401, detail="Invalid email or password")

    # Check account lockout
    if account.locked_until and account.locked_until > datetime.now(timezone.utc):
        remaining = int((account.locked_until - datetime.now(timezone.utc)).total_seconds() / 60) + 1
        raise HTTPException(
            status_code=423,
            detail=f"Account is locked due to too many failed attempts. Try again in {remaining} minutes.",
        )

    if not verify_password(req.password, account.password_hash):
        log_login_failure(req.email)
        account.failed_login_attempts = (account.failed_login_attempts or 0) + 1
        if account.failed_login_attempts >= LOCKOUT_THRESHOLD:
            account.locked_until = datetime.now(timezone.utc) + timedelta(minutes=LOCKOUT_DURATION_MINUTES)
        db.commit()
        raise HTTPException(status_code=401, detail="Invalid email or password")

    # Reset failed attempts on successful login
    account.failed_login_attempts = 0
    account.locked_until = None
    db.commit()

    access_token = create_access_token(account.id)
    refresh_token = create_refresh_token(account.id)
    csrf_token = _generate_csrf_token()
    log_auth_success(account.id)

    _set_auth_cookies(response, access_token, refresh_token, csrf_token)

    return AuthResponse(
        access_token=access_token,
        account_id=account.id,
        account_name=account.name,
        email=account.email,
        country=account.country,
        language=account.language,
    )


@router.post("/auth/refresh")
@limiter.limit("10/minute")
def refresh(request: Request, response: Response, db: Session = Depends(get_db)):
    token = request.cookies.get("refresh_token")
    if not token:
        raise HTTPException(status_code=401, detail="No refresh token")

    account_id = decode_refresh_token(token)
    account = db.query(Account).filter(
        Account.id == account_id,
        Account.is_active.is_(True),
    ).first()
    if not account:
        raise HTTPException(status_code=401, detail="Account not found or inactive")

    access_token = create_access_token(account.id)
    refresh_token = create_refresh_token(account.id)
    csrf_token = _generate_csrf_token()

    _set_auth_cookies(response, access_token, refresh_token, csrf_token)

    return {
        "account_id": account.id,
        "account_name": account.name,
        "email": account.email,
        "country": account.country,
        "language": account.language,
    }


@router.post("/auth/logout")
def logout(response: Response):
    _clear_auth_cookies(response)
    return {"detail": "Logged out"}


@router.get("/auth/me")
@limiter.limit("30/minute")
def get_me(request: Request, account: Account = Depends(get_current_account)):
    return {
        "account_id": account.id,
        "account_name": account.name,
        "email": account.email,
        "country": account.country,
        "language": account.language,
    }


@router.post("/auth/reset-password")
def reset_password(req: ResetPasswordRequest, db: Session = Depends(get_db)):
    _validate_password(req.new_password)

    account = db.query(Account).filter(Account.email == req.email, Account.is_active.is_(True)).first()
    if not account:
        return {"detail": "If an account with that email exists, the password has been reset."}

    account.password_hash = hash_password(req.new_password)
    account.failed_login_attempts = 0
    account.locked_until = None
    db.commit()

    return {"detail": "If an account with that email exists, the password has been reset."}
