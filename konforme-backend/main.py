import secrets

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from starlette.middleware.base import BaseHTTPMiddleware

from config import settings
from database import Base, engine
from rate_limit import limiter
from routers import accounts, assessment, remediation, scans, score
from routers.auth_router import router as auth_router

# Paths exempt from CSRF validation (login/register need to work without a prior CSRF token)
CSRF_EXEMPT_PATHS = {
    "/api/v1/auth/login",
    "/api/v1/auth/register",
    "/api/v1/auth/reset-password",
    "/api/v1/auth/refresh",
}

CSRF_METHODS = {"POST", "PATCH", "DELETE", "PUT"}


class CSRFMiddleware(BaseHTTPMiddleware):
    """Double-submit cookie CSRF protection.

    Non-httpOnly `csrf_token` cookie is validated against `X-CSRF-Token` header
    on state-changing requests. Login/register are exempt since they issue the cookie.
    """

    async def dispatch(self, request: Request, call_next):
        if request.method in CSRF_METHODS and request.url.path not in CSRF_EXEMPT_PATHS:
            cookie_token = request.cookies.get("csrf_token")
            header_token = request.headers.get("x-csrf-token")
            if not cookie_token or not header_token or not secrets.compare_digest(cookie_token, header_token):
                return Response(
                    content='{"detail":"CSRF validation failed"}',
                    status_code=403,
                    media_type="application/json",
                )
        return await call_next(request)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains"

        allowed_origins = " ".join(settings.origins_list)
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data:; "
            f"connect-src 'self' {allowed_origins}; "
            "font-src 'self'; "
            "frame-ancestors 'none'"
        )
        response.headers["Cache-Control"] = "no-store"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        return response


app = FastAPI(
    title="Konforme API",
    description="NIS2 compliance scanning and assessment backend",
    version="1.0.0",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["Content-Type", "Authorization", "X-CSRF-Token", "Accept"],
)

# CSRF protection (must be added after CORS so CORS preflight passes)
app.add_middleware(CSRFMiddleware)

# Security headers
app.add_middleware(SecurityHeadersMiddleware)

# Rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Routers
app.include_router(auth_router, prefix="/api/v1", tags=["Auth"])
app.include_router(accounts.router, prefix="/api/v1", tags=["Accounts"])
app.include_router(scans.router, prefix="/api/v1", tags=["Scans"])
app.include_router(assessment.router, prefix="/api/v1", tags=["Assessment"])
app.include_router(score.router, prefix="/api/v1", tags=["Score & Report"])
app.include_router(remediation.router, prefix="/api/v1", tags=["Remediation"])


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "konforme-api"}


WEAK_SECRET_KEYS = {"change-me", "change-me-to-a-random-string", "secret", ""}


@app.on_event("startup")
def on_startup():
    # Production safety checks
    if settings.environment == "production":
        if settings.secret_key in WEAK_SECRET_KEYS or len(settings.secret_key) < 32:
            raise RuntimeError(
                "SECRET_KEY is too weak for production. "
                "Set SECRET_KEY to a random string of at least 32 characters. "
                "Generate one with: python -c \"import secrets; print(secrets.token_urlsafe(64))\""
            )
        if not settings.encryption_key:
            raise RuntimeError(
                "ENCRYPTION_KEY is not set. Required for production. "
                "Generate one with: python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\""
            )

    Base.metadata.create_all(bind=engine)
