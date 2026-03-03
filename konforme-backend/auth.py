from datetime import datetime, timedelta, timezone

import bcrypt
from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from config import settings
from database import get_db
from models import Account

bearer_scheme = HTTPBearer(auto_error=False)


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


def create_access_token(account_id: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)
    payload = {"sub": account_id, "exp": expire, "type": "access"}
    return jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)


def create_refresh_token(account_id: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_expire_days)
    payload = {"sub": account_id, "exp": expire, "type": "refresh"}
    return jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> str:
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])
        token_type = payload.get("type", "access")
        if token_type != "access":
            raise HTTPException(status_code=401, detail="Invalid token type")
        account_id: str | None = payload.get("sub")
        if account_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return account_id
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")


def decode_refresh_token(token: str) -> str:
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])
        token_type = payload.get("type")
        if token_type != "refresh":
            raise HTTPException(status_code=401, detail="Invalid token type")
        account_id: str | None = payload.get("sub")
        if account_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return account_id
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")


def _extract_token(request: Request, credentials: HTTPAuthorizationCredentials | None) -> str | None:
    """Extract access token from Authorization header first, then fall back to cookie."""
    if credentials:
        return credentials.credentials
    token = request.cookies.get("access_token")
    if token:
        return token
    return None


def get_current_account(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> Account:
    token = _extract_token(request, credentials)
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    account_id = decode_access_token(token)
    account = db.query(Account).filter(
        Account.id == account_id,
        Account.is_active.is_(True),
    ).first()
    if not account:
        raise HTTPException(status_code=401, detail="Account not found or inactive")
    return account


def enforce_account_access(account: Account, account_id: str) -> None:
    if account.id != account_id:
        raise HTTPException(status_code=403, detail="Access denied")
