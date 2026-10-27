import secrets

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from starlette.middleware.base import BaseHTTPMiddleware

from config import settings
from database import SessionLocal
from rate_limit import limiter
from routers import accounts, assessment, audit_log, business_processes, cloud_credentials, controls, countries, evidence, mappings, people_tasks, remediation, reports, scans, score
from routers import settings as settings_router
from routers import team
from routers.auth_router import router as auth_router

# Paths exempt from CSRF validation (login/register need to work without a prior CSRF token)
CSRF_EXEMPT_PATHS = {
    "/api/v1/auth/login",
    "/api/v1/auth/register",
    "/api/v1/auth/forgot-password",
    "/api/v1/auth/reset-password",
    "/api/v1/auth/verify-email",
    "/api/v1/auth/refresh",
    "/api/v1/team/accept-invite",
}

# Dynamic CSRF exemption for paths with tokens or OAuth callbacks
CSRF_EXEMPT_PREFIXES = (
    "/api/v1/campaigns/tasks/complete/",
    "/api/v1/cloud-credentials/azure/callback",
)

CSRF_METHODS = {"POST", "PATCH", "DELETE", "PUT"}


class CSRFMiddleware(BaseHTTPMiddleware):
    """Double-submit cookie CSRF protection.

    Non-httpOnly `csrf_token` cookie is validated against `X-CSRF-Token` header
    on state-changing requests. Login/register are exempt since they issue the cookie.
    """

    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        is_exempt = path in CSRF_EXEMPT_PATHS or any(path.startswith(p) for p in CSRF_EXEMPT_PREFIXES)
        if request.method in CSRF_METHODS and not is_exempt:
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


_is_production = settings.environment == "production"

app = FastAPI(
    title="Konforme API",
    description="NIS2 compliance scanning and assessment backend",
    version="1.0.0",
    docs_url=None if _is_production else "/docs",
    redoc_url=None if _is_production else "/redoc",
    openapi_url=None if _is_production else "/openapi.json",
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
app.include_router(countries.router, prefix="/api/v1", tags=["Countries"])
app.include_router(scans.router, prefix="/api/v1", tags=["Scans"])
app.include_router(cloud_credentials.router, prefix="/api/v1", tags=["Cloud Credentials"])
app.include_router(assessment.router, prefix="/api/v1", tags=["Assessment"])
app.include_router(score.router, prefix="/api/v1", tags=["Score & Report"])
app.include_router(remediation.router, prefix="/api/v1", tags=["Remediation"])
app.include_router(evidence.router, prefix="/api/v1", tags=["Evidence"])
app.include_router(controls.router, prefix="/api/v1", tags=["Controls"])
app.include_router(settings_router.router, prefix="/api/v1", tags=["Settings"])
app.include_router(team.router, prefix="/api/v1", tags=["Team"])
app.include_router(business_processes.router, prefix="/api/v1", tags=["Business Processes"])
app.include_router(audit_log.router, prefix="/api/v1", tags=["Audit Log"])
app.include_router(mappings.router, prefix="/api/v1", tags=["Mappings"])
app.include_router(people_tasks.router, prefix="/api/v1", tags=["People Tasks"])
app.include_router(reports.router, prefix="/api/v1", tags=["Reports"])


@app.get("/health")
def health_check():
    from store import ping
    try:
        ping()
        db_status = "connected"
    except Exception:
        db_status = "unavailable"
    status = "ok" if db_status == "connected" else "degraded"
    return {"status": status, "service": "konforme-api", "database": db_status}


WEAK_SECRET_KEYS = {"change-me", "change-me-to-a-random-string", "secret", ""}


def check_production_settings():
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
        if not settings.cookie_secure:
            raise RuntimeError(
                "COOKIE_SECURE must be True in production to prevent cookies being sent over HTTP."
            )


def bootstrap_database():
    # Seed reference data (idempotent). The table itself is created by Terraform.
    from scripts.seed_base_controls import seed_base_controls
    from scripts.seed_question_control_mappings import seed_question_control_mappings
    from scripts.seed_countries import DATA_DIR as COUNTRIES_DIR, seed_country
    from scripts.seed_country_data import seed_country_data
    with SessionLocal() as db:
        seed_base_controls(db)
        seed_question_control_mappings(db)

    country_files = sorted(f for f in COUNTRIES_DIR.glob("*.json") if f.name != "_index.json")
    # Countries first: country controls/questions look their country up
    with SessionLocal() as db:
        for filepath in country_files:
            seed_country(db, filepath)
        db.commit()
    with SessionLocal() as db:
        for filepath in country_files:
            seed_country_data(db, filepath)
        db.commit()


# Not used on Lambda (see lambda_handler.py): there, seeding runs in the migrate
# function and the daily jobs are triggered by EventBridge Scheduler.
@app.on_event("startup")
def on_startup():
    check_production_settings()
    bootstrap_database()

    # Start background scheduler (overdue reminders, chronic slip escalation)
    from scheduler import start_scheduler
    start_scheduler()


@app.on_event("shutdown")
def on_shutdown():
    from scheduler import stop_scheduler
    stop_scheduler()
