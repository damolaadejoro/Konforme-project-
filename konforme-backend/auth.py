from datetime import datetime, timedelta, timezone

import bcrypt
from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from config import settings
from database import get_db
from models import Account, User, UserRole

bearer_scheme = HTTPBearer(auto_error=False)


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


def create_access_token(account_id: str, user_id: str | None = None) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)
    payload = {"sub": account_id, "exp": expire, "type": "access"}
    if user_id:
        payload["user_id"] = user_id
    return jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)


def create_refresh_token(account_id: str, user_id: str | None = None) -> str:
    expire = datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_expire_days)
    payload = {"sub": account_id, "exp": expire, "type": "refresh"}
    if user_id:
        payload["user_id"] = user_id
    return jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict:
    """Decode access token, returning {'account_id': ..., 'user_id': ...}."""
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])
        token_type = payload.get("type", "access")
        if token_type != "access":
            raise HTTPException(status_code=401, detail="Invalid token type")
        account_id: str | None = payload.get("sub")
        if account_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return {"account_id": account_id, "user_id": payload.get("user_id")}
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")


def decode_refresh_token(token: str) -> dict:
    """Decode refresh token, returning {'account_id': ..., 'user_id': ...}."""
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])
        token_type = payload.get("type")
        if token_type != "refresh":
            raise HTTPException(status_code=401, detail="Invalid token type")
        account_id: str | None = payload.get("sub")
        if account_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return {"account_id": account_id, "user_id": payload.get("user_id")}
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


def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    """Get the authenticated User. Falls back to account-level auth for backward compatibility."""
    token = _extract_token(request, credentials)
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    token_data = decode_access_token(token)

    # Try user_id first (new tokens)
    user_id = token_data.get("user_id")
    if user_id:
        user = db.query(User).filter(User.id == user_id, User.is_active.is_(True)).first()
        if user:
            return user

    # Fallback: find the owner user for this account (backward compat with old tokens)
    account_id = token_data["account_id"]
    user = (
        db.query(User)
        .filter(User.account_id == account_id, User.is_active.is_(True))
        .order_by(User.created_at)
        .first()
    )
    if not user:
        raise HTTPException(status_code=401, detail="User not found or inactive")
    return user


def get_current_account(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> Account:
    """Bridge dependency — returns the Account via the User. Backward compatible."""
    token = _extract_token(request, credentials)
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    token_data = decode_access_token(token)
    account_id = token_data["account_id"]

    account = db.query(Account).filter(
        Account.id == account_id,
        Account.is_active.is_(True),
    ).first()
    if not account:
        raise HTTPException(status_code=401, detail="Account not found or inactive")
    return account


def require_role(*allowed_roles: UserRole):
    """Dependency factory: require the current user to have one of the specified roles."""
    def dependency(user: User = Depends(get_current_user)) -> User:
        if user.role not in [r.value for r in allowed_roles]:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return user
    return dependency


def enforce_account_access(account: Account, account_id: str) -> None:
    if account.id != account_id:
        raise HTTPException(status_code=403, detail="Access denied")
