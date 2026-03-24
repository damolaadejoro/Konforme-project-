from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from config import settings


def _build_engine():
    url = settings.database_url

    if url.startswith("sqlite"):
        return create_engine(
            url,
            connect_args={"check_same_thread": False},
        )

    # PostgreSQL (or other non-SQLite databases)
    kwargs = {
        "pool_pre_ping": True,
        "pool_size": settings.database_pool_size,
        "max_overflow": settings.database_max_overflow,
        "pool_timeout": settings.database_pool_timeout,
    }

    if settings.environment == "production" and "postgresql" in url:
        if "sslmode" not in url:
            separator = "&" if "?" in url else "?"
            url = f"{url}{separator}sslmode=require"

    return create_engine(url, **kwargs)


engine = _build_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def run_migrations(eng):
    """Idempotent column additions for existing tables."""
    from sqlalchemy import inspect as sa_inspect, text

    inspector = sa_inspect(eng)
    if "accounts" in inspector.get_table_names():
        existing = {c["name"] for c in inspector.get_columns("accounts")}
        with eng.begin() as conn:
            if "country" not in existing:
                conn.execute(text("ALTER TABLE accounts ADD COLUMN country VARCHAR(2)"))
            if "language" not in existing:
                conn.execute(text("ALTER TABLE accounts ADD COLUMN language VARCHAR(5) DEFAULT 'en'"))
            if "country_id" not in existing:
                conn.execute(text("ALTER TABLE accounts ADD COLUMN country_id VARCHAR(36)"))
            if "entity_tier_id" not in existing:
                conn.execute(text("ALTER TABLE accounts ADD COLUMN entity_tier_id VARCHAR(36)"))
            if "scoring_config" not in existing:
                conn.execute(text("ALTER TABLE accounts ADD COLUMN scoring_config TEXT"))
            if "email_verified" not in existing:
                conn.execute(text("ALTER TABLE accounts ADD COLUMN email_verified BOOLEAN DEFAULT false"))
            # email_verification_token removed from accounts (now on users table only)

    # Users table — created by migration 006 but ensure it exists for non-Alembic setups
    if "users" not in inspector.get_table_names():
        with eng.begin() as conn:
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS users (
                    id VARCHAR(36) PRIMARY KEY,
                    account_id VARCHAR(36) NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
                    name VARCHAR(255) NOT NULL,
                    email VARCHAR(255) UNIQUE NOT NULL,
                    password_hash VARCHAR(255),
                    role VARCHAR(20) DEFAULT 'member' NOT NULL,
                    email_verified BOOLEAN DEFAULT false NOT NULL,
                    email_verification_token VARCHAR(36),
                    invite_token VARCHAR(36) UNIQUE,
                    invite_accepted_at TIMESTAMP,
                    is_active BOOLEAN DEFAULT true NOT NULL,
                    failed_login_attempts INTEGER DEFAULT 0 NOT NULL,
                    locked_until TIMESTAMP,
                    password_reset_token VARCHAR(64),
                    password_reset_expires TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
                )
            """))

    # Security hardening: token expiry columns and wider token fields
    is_postgres = "postgresql" in str(eng.url)
    if "users" in inspector.get_table_names():
        existing = {c["name"] for c in inspector.get_columns("users")}
        with eng.begin() as conn:
            if "email_verification_expires" not in existing:
                conn.execute(text("ALTER TABLE users ADD COLUMN email_verification_expires TIMESTAMP"))
            if "invite_expires" not in existing:
                conn.execute(text("ALTER TABLE users ADD COLUMN invite_expires TIMESTAMP"))
            # Widen token columns for secrets.token_urlsafe(32) (~43 chars)
            if is_postgres:
                conn.execute(text("ALTER TABLE users ALTER COLUMN email_verification_token TYPE VARCHAR(64)"))
                conn.execute(text("ALTER TABLE users ALTER COLUMN invite_token TYPE VARCHAR(64)"))

    if "campaign_tasks" in inspector.get_table_names():
        existing = {c["name"] for c in inspector.get_columns("campaign_tasks")}
        with eng.begin() as conn:
            if "completion_token" not in existing:
                conn.execute(text("ALTER TABLE campaign_tasks ADD COLUMN completion_token VARCHAR(64)"))
            elif is_postgres:
                conn.execute(text("ALTER TABLE campaign_tasks ALTER COLUMN completion_token TYPE VARCHAR(64)"))

    if "scans" in inspector.get_table_names():
        existing = {c["name"] for c in inspector.get_columns("scans")}
        with eng.begin() as conn:
            if "provider" not in existing:
                conn.execute(text("ALTER TABLE scans ADD COLUMN provider VARCHAR(20) DEFAULT 'aws'"))
            if "cloud_credential_id" not in existing:
                conn.execute(text("ALTER TABLE scans ADD COLUMN cloud_credential_id VARCHAR(36)"))
            if "aws_account_id" not in existing:
                conn.execute(text("ALTER TABLE scans ADD COLUMN aws_account_id VARCHAR(36)"))


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
