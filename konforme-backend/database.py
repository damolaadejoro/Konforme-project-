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
