from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from config import settings


def _build_engine():
    url = settings.database_url

    # Render (and some other platforms) provide postgres:// but SQLAlchemy requires postgresql://
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)

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
                    email_verification_token VARCHAR(64),
                    email_verification_expires TIMESTAMPTZ,
                    invite_token VARCHAR(64) UNIQUE,
                    invite_expires TIMESTAMPTZ,
                    invite_accepted_at TIMESTAMPTZ,
                    is_active BOOLEAN DEFAULT true NOT NULL,
                    failed_login_attempts INTEGER DEFAULT 0 NOT NULL,
                    locked_until TIMESTAMPTZ,
                    password_reset_token VARCHAR(64),
                    password_reset_expires TIMESTAMPTZ,
                    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
                    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL
                )
            """))

    # Security hardening: token expiry columns and wider token fields
    is_postgres = "postgresql" in str(eng.url)
    ts_type = "TIMESTAMPTZ" if is_postgres else "TIMESTAMP"
    if "users" in inspector.get_table_names():
        existing = {c["name"] for c in inspector.get_columns("users")}
        with eng.begin() as conn:
            if "email_verification_expires" not in existing:
                conn.execute(text(f"ALTER TABLE users ADD COLUMN email_verification_expires {ts_type}"))
            elif is_postgres:
                conn.execute(text("ALTER TABLE users ALTER COLUMN email_verification_expires TYPE TIMESTAMPTZ"))
            if "invite_expires" not in existing:
                conn.execute(text(f"ALTER TABLE users ADD COLUMN invite_expires {ts_type}"))
            elif is_postgres:
                conn.execute(text("ALTER TABLE users ALTER COLUMN invite_expires TYPE TIMESTAMPTZ"))
        # Widen token columns in a separate transaction (avoid rollback if ALTER fails)
        if is_postgres:
            try:
                with eng.begin() as conn:
                    conn.execute(text("ALTER TABLE users ALTER COLUMN email_verification_token TYPE VARCHAR(64)"))
                    conn.execute(text("ALTER TABLE users ALTER COLUMN invite_token TYPE VARCHAR(64)"))
            except Exception:
                pass  # Already correct width or unsupported

    if "campaign_tasks" in inspector.get_table_names():
        existing = {c["name"] for c in inspector.get_columns("campaign_tasks")}
        with eng.begin() as conn:
            if "completion_token" not in existing:
                conn.execute(text("ALTER TABLE campaign_tasks ADD COLUMN completion_token VARCHAR(64)"))
            elif is_postgres:
                try:
                    conn.execute(text("ALTER TABLE campaign_tasks ALTER COLUMN completion_token TYPE VARCHAR(64)"))
                except Exception:
                    pass

    if "scans" in inspector.get_table_names():
        existing = {c["name"] for c in inspector.get_columns("scans")}
        with eng.begin() as conn:
            if "provider" not in existing:
                conn.execute(text("ALTER TABLE scans ADD COLUMN provider VARCHAR(20) DEFAULT 'aws'"))
            if "cloud_credential_id" not in existing:
                conn.execute(text("ALTER TABLE scans ADD COLUMN cloud_credential_id VARCHAR(36)"))
            if "aws_account_id" not in existing:
                conn.execute(text("ALTER TABLE scans ADD COLUMN aws_account_id VARCHAR(36)"))

    # Cloud credentials — new role/OAuth fields
    if "cloud_credentials" in inspector.get_table_names():
        existing = {c["name"] for c in inspector.get_columns("cloud_credentials")}
        with eng.begin() as conn:
            if "aws_role_arn" not in existing:
                conn.execute(text("ALTER TABLE cloud_credentials ADD COLUMN aws_role_arn VARCHAR(2048)"))
            if "aws_external_id" not in existing:
                conn.execute(text("ALTER TABLE cloud_credentials ADD COLUMN aws_external_id VARCHAR(512)"))
            if "aws_connection_type" not in existing:
                conn.execute(text("ALTER TABLE cloud_credentials ADD COLUMN aws_connection_type VARCHAR(20) DEFAULT 'keys'"))
            if "azure_connection_type" not in existing:
                conn.execute(text("ALTER TABLE cloud_credentials ADD COLUMN azure_connection_type VARCHAR(20) DEFAULT 'client_secret'"))

    # Business processes table
    if "business_processes" not in inspector.get_table_names():
        with eng.begin() as conn:
            conn.execute(text(f"""
                CREATE TABLE business_processes (
                    id VARCHAR(36) PRIMARY KEY,
                    account_id VARCHAR(36) NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
                    name VARCHAR(255) NOT NULL,
                    description TEXT DEFAULT '',
                    is_critical BOOLEAN DEFAULT true,
                    owner VARCHAR(255) DEFAULT '',
                    created_at {ts_type} DEFAULT CURRENT_TIMESTAMP NOT NULL,
                    updated_at {ts_type} DEFAULT CURRENT_TIMESTAMP NOT NULL
                )
            """))

    # Process-control linking table
    if "process_controls" not in inspector.get_table_names():
        with eng.begin() as conn:
            conn.execute(text(f"""
                CREATE TABLE process_controls (
                    id VARCHAR(36) PRIMARY KEY,
                    business_process_id VARCHAR(36) NOT NULL REFERENCES business_processes(id) ON DELETE CASCADE,
                    control_id VARCHAR(100) NOT NULL,
                    applicable BOOLEAN DEFAULT true,
                    justification TEXT DEFAULT '',
                    created_at {ts_type} DEFAULT CURRENT_TIMESTAMP NOT NULL,
                    UNIQUE (business_process_id, control_id)
                )
            """))

    # OAuth state table for Azure admin consent flow
    if "oauth_states" not in inspector.get_table_names():
        with eng.begin() as conn:
            conn.execute(text("""
                CREATE TABLE oauth_states (
                    id VARCHAR(36) PRIMARY KEY,
                    account_id VARCHAR(36) NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
                    state_token VARCHAR(128) UNIQUE NOT NULL,
                    provider VARCHAR(20) NOT NULL,
                    alias VARCHAR(255) NOT NULL,
                    subscription_id VARCHAR(512),
                    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
                    expires_at TIMESTAMPTZ NOT NULL
                )
            """))

    # --- Phase 2: Evidence overhaul, evidence_links, assessment_question_controls, audit_log ---

    # Evidence table — new columns
    if "evidence" in inspector.get_table_names():
        existing = {c["name"] for c in inspector.get_columns("evidence")}
        with eng.begin() as conn:
            if "s3_key" not in existing:
                conn.execute(text("ALTER TABLE evidence ADD COLUMN s3_key VARCHAR(1000)"))
            if "sha256" not in existing:
                conn.execute(text("ALTER TABLE evidence ADD COLUMN sha256 VARCHAR(64)"))
            if "description" not in existing:
                conn.execute(text("ALTER TABLE evidence ADD COLUMN description TEXT DEFAULT ''"))
            if "tags" not in existing:
                conn.execute(text("ALTER TABLE evidence ADD COLUMN tags TEXT DEFAULT '[]'"))
            if "retention_until" not in existing:
                conn.execute(text("ALTER TABLE evidence ADD COLUMN retention_until DATE"))
            if "deleted_at" not in existing:
                conn.execute(text(f"ALTER TABLE evidence ADD COLUMN deleted_at {ts_type}"))
            if "uploaded_by_user_id" not in existing:
                conn.execute(text("ALTER TABLE evidence ADD COLUMN uploaded_by_user_id VARCHAR(36)"))
        # Make control_id nullable (separate transaction)
        if is_postgres:
            try:
                with eng.begin() as conn:
                    conn.execute(text("ALTER TABLE evidence ALTER COLUMN control_id DROP NOT NULL"))
            except Exception:
                pass

    # Evidence links table
    if "evidence_links" not in inspector.get_table_names():
        with eng.begin() as conn:
            conn.execute(text(f"""
                CREATE TABLE evidence_links (
                    id VARCHAR(36) PRIMARY KEY,
                    evidence_id VARCHAR(36) NOT NULL REFERENCES evidence(id) ON DELETE CASCADE,
                    entity_type VARCHAR(50) NOT NULL,
                    entity_id VARCHAR(100) NOT NULL,
                    link_type VARCHAR(20) DEFAULT 'primary',
                    linked_by_user_id VARCHAR(36),
                    linked_at {ts_type} DEFAULT CURRENT_TIMESTAMP NOT NULL,
                    unlinked_at {ts_type},
                    UNIQUE (evidence_id, entity_type, entity_id)
                )
            """))

        # Migrate existing evidence rows: create evidence_links from control_id
        if "evidence" in inspector.get_table_names():
            try:
                with eng.begin() as conn:
                    conn.execute(text("""
                        INSERT INTO evidence_links (id, evidence_id, entity_type, entity_id, link_type, linked_at)
                        SELECT
                            id || '-link' AS id,
                            id AS evidence_id,
                            'control' AS entity_type,
                            control_id AS entity_id,
                            'primary' AS link_type,
                            uploaded_at AS linked_at
                        FROM evidence
                        WHERE control_id IS NOT NULL AND control_id != ''
                    """))
            except Exception:
                pass  # Migration may have already run or no data

    # Assessment-question-control mapping table
    if "assessment_question_controls" not in inspector.get_table_names():
        with eng.begin() as conn:
            conn.execute(text(f"""
                CREATE TABLE assessment_question_controls (
                    id VARCHAR(36) PRIMARY KEY,
                    question_id VARCHAR(50) NOT NULL,
                    control_id VARCHAR(100) NOT NULL,
                    weight REAL DEFAULT 1.0,
                    created_at {ts_type} DEFAULT CURRENT_TIMESTAMP NOT NULL,
                    UNIQUE (question_id, control_id)
                )
            """))

    # Audit log table
    auto_pk = "BIGSERIAL PRIMARY KEY" if is_postgres else "INTEGER PRIMARY KEY AUTOINCREMENT"
    if "audit_log" not in inspector.get_table_names():
        with eng.begin() as conn:
            conn.execute(text(f"""
                CREATE TABLE audit_log (
                    id {auto_pk},
                    account_id VARCHAR(36),
                    event_type VARCHAR(120) NOT NULL,
                    event_category VARCHAR(50) NOT NULL,
                    actor_user_id VARCHAR(36),
                    actor_email VARCHAR(255),
                    actor_ip VARCHAR(45),
                    entity_type VARCHAR(100),
                    entity_id VARCHAR(100),
                    entity_label VARCHAR(300),
                    correlation_id VARCHAR(36),
                    before_state TEXT,
                    after_state TEXT,
                    change_reason TEXT,
                    is_material BOOLEAN DEFAULT false,
                    metadata_json TEXT,
                    occurred_at {ts_type} DEFAULT CURRENT_TIMESTAMP NOT NULL,
                    hash VARCHAR(64) NOT NULL,
                    prev_hash VARCHAR(64)
                )
            """))

    # --- Phase 3: Remediation plans, plan milestones, plan links, pending people tasks ---

    # Remediation plans table
    if "remediation_plans" not in inspector.get_table_names():
        with eng.begin() as conn:
            conn.execute(text(f"""
                CREATE TABLE remediation_plans (
                    id VARCHAR(36) PRIMARY KEY,
                    account_id VARCHAR(36) NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
                    title VARCHAR(500) NOT NULL,
                    description TEXT DEFAULT '',
                    treatment_type VARCHAR(20) NOT NULL DEFAULT 'mitigate',
                    status VARCHAR(30) DEFAULT 'draft',
                    target_date DATE,
                    created_by_user_id VARCHAR(36) REFERENCES users(id),
                    approved_by_user_id VARCHAR(36) REFERENCES users(id),
                    approved_at {ts_type},
                    rejected_by_user_id VARCHAR(36) REFERENCES users(id),
                    rejected_at {ts_type},
                    rejection_reason TEXT,
                    created_at {ts_type} DEFAULT CURRENT_TIMESTAMP NOT NULL,
                    updated_at {ts_type} DEFAULT CURRENT_TIMESTAMP NOT NULL
                )
            """))

    # Remediation plan milestones
    if "remediation_plan_milestones" not in inspector.get_table_names():
        with eng.begin() as conn:
            conn.execute(text(f"""
                CREATE TABLE remediation_plan_milestones (
                    id VARCHAR(36) PRIMARY KEY,
                    plan_id VARCHAR(36) NOT NULL REFERENCES remediation_plans(id) ON DELETE CASCADE,
                    title VARCHAR(500) NOT NULL,
                    description TEXT DEFAULT '',
                    target_date DATE,
                    completed_at {ts_type},
                    display_order INTEGER DEFAULT 0,
                    created_at {ts_type} DEFAULT CURRENT_TIMESTAMP NOT NULL
                )
            """))

    # Remediation plan links (to controls/questions/processes)
    if "remediation_plan_links" not in inspector.get_table_names():
        with eng.begin() as conn:
            conn.execute(text(f"""
                CREATE TABLE remediation_plan_links (
                    id VARCHAR(36) PRIMARY KEY,
                    plan_id VARCHAR(36) NOT NULL REFERENCES remediation_plans(id) ON DELETE CASCADE,
                    entity_type VARCHAR(50) NOT NULL,
                    entity_id VARCHAR(100) NOT NULL,
                    created_at {ts_type} DEFAULT CURRENT_TIMESTAMP NOT NULL,
                    UNIQUE (plan_id, entity_type, entity_id)
                )
            """))

    # Pending people task instantiations (Phase 4 queue)
    if "pending_people_task_instantiations" not in inspector.get_table_names():
        with eng.begin() as conn:
            conn.execute(text(f"""
                CREATE TABLE pending_people_task_instantiations (
                    id VARCHAR(36) PRIMARY KEY,
                    account_id VARCHAR(36) NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
                    control_id VARCHAR(100) NOT NULL,
                    task_type VARCHAR(20) NOT NULL DEFAULT 'acknowledge',
                    source_plan_id VARCHAR(36) REFERENCES remediation_plans(id),
                    source_task_id VARCHAR(36) REFERENCES remediation_tasks(id),
                    status VARCHAR(20) DEFAULT 'pending',
                    created_at {ts_type} DEFAULT CURRENT_TIMESTAMP NOT NULL,
                    instantiated_at {ts_type}
                )
            """))

    # ALTER remediation_tasks — add Phase 3 columns
    if "remediation_tasks" in inspector.get_table_names():
        existing = {c["name"] for c in inspector.get_columns("remediation_tasks")}
        phase3_cols = [
            ("plan_id", "VARCHAR(36)"),
            ("related_control_id", "VARCHAR(100)"),
            ("related_assessment_answer_id", "VARCHAR(36)"),
            ("severity", "VARCHAR(20) DEFAULT 'medium'"),
            ("auto_generated", "BOOLEAN DEFAULT false"),
            ("closure_evidence_id", "VARCHAR(36)"),
            ("closure_note", "TEXT"),
            ("closed_by_user_id", "VARCHAR(36)"),
            ("dismissed_reason", "TEXT"),
            ("dismissed_by_user_id", "VARCHAR(36)"),
            ("dismissed_at", ts_type),
            ("original_due_date", "DATE"),
            ("reschedule_count", "INTEGER DEFAULT 0"),
        ]
        for col_name, col_type in phase3_cols:
            if col_name not in existing:
                try:
                    with eng.begin() as conn:
                        conn.execute(text(f"ALTER TABLE remediation_tasks ADD COLUMN {col_name} {col_type}"))
                except Exception:
                    pass

    # --- Phase 4: People tasks — continuous compliance ---

    if "people_tasks" not in inspector.get_table_names():
        with eng.begin() as conn:
            conn.execute(text(f"""
                CREATE TABLE people_tasks (
                    id VARCHAR(36) PRIMARY KEY,
                    account_id VARCHAR(36) NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
                    title VARCHAR(500) NOT NULL,
                    description TEXT DEFAULT '',
                    task_type VARCHAR(30) NOT NULL,
                    pdca_phase VARCHAR(10) NOT NULL,
                    article_21_subsection VARCHAR(5) NOT NULL,
                    frequency VARCHAR(20) NOT NULL,
                    next_due_date DATE,
                    assignee_user_id VARCHAR(36) REFERENCES users(id),
                    assignee_role VARCHAR(50),
                    related_control_id VARCHAR(100),
                    related_process_id VARCHAR(36) REFERENCES business_processes(id) ON DELETE SET NULL,
                    related_plan_id VARCHAR(36) REFERENCES remediation_plans(id) ON DELETE SET NULL,
                    requires_evidence BOOLEAN DEFAULT false,
                    attestation_statement TEXT,
                    baseline_template_id VARCHAR(100),
                    active BOOLEAN DEFAULT true,
                    created_at {ts_type} DEFAULT CURRENT_TIMESTAMP NOT NULL,
                    updated_at {ts_type} DEFAULT CURRENT_TIMESTAMP NOT NULL
                )
            """))

    # Add isms_domain column if missing
    if "people_tasks" in inspector.get_table_names():
        existing_pt_cols = {c["name"] for c in inspector.get_columns("people_tasks")}
        if "isms_domain" not in existing_pt_cols:
            with eng.begin() as conn:
                conn.execute(text("ALTER TABLE people_tasks ADD COLUMN isms_domain VARCHAR(50)"))

    if "people_task_completions" not in inspector.get_table_names():
        with eng.begin() as conn:
            conn.execute(text(f"""
                CREATE TABLE people_task_completions (
                    id VARCHAR(36) PRIMARY KEY,
                    people_task_id VARCHAR(36) NOT NULL REFERENCES people_tasks(id) ON DELETE CASCADE,
                    user_id VARCHAR(36) NOT NULL REFERENCES users(id),
                    period_key VARCHAR(20) NOT NULL,
                    attested_at {ts_type},
                    attestation_response TEXT,
                    evidence_id VARCHAR(36) REFERENCES evidence(id) ON DELETE SET NULL,
                    created_at {ts_type} DEFAULT CURRENT_TIMESTAMP NOT NULL,
                    UNIQUE (people_task_id, user_id, period_key)
                )
            """))

    # --- Phase 5: Reports archive ---

    if "reports" not in inspector.get_table_names():
        with eng.begin() as conn:
            conn.execute(text(f"""
                CREATE TABLE reports (
                    id VARCHAR(36) PRIMARY KEY,
                    account_id VARCHAR(36) NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
                    document_id VARCHAR(50) UNIQUE NOT NULL,
                    period VARCHAR(20) NOT NULL,
                    period_start DATE NOT NULL,
                    period_end DATE NOT NULL,
                    aggregate_score REAL NOT NULL,
                    technical_score REAL NOT NULL,
                    human_factor_score REAL NOT NULL,
                    grade VARCHAR(2) NOT NULL,
                    maturity_level INTEGER NOT NULL DEFAULT 1,
                    file_size_bytes INTEGER NOT NULL DEFAULT 0,
                    file_path VARCHAR(1000),
                    content_hash VARCHAR(64),
                    generated_at {ts_type} DEFAULT CURRENT_TIMESTAMP NOT NULL,
                    generated_by_user_id VARCHAR(36) REFERENCES users(id)
                )
            """))

    # Add columns to reports if created before upgrade
    if "reports" in inspector.get_table_names():
        existing_rpt = {c["name"] for c in inspector.get_columns("reports")}
        with eng.begin() as conn:
            if "maturity_level" not in existing_rpt:
                conn.execute(text("ALTER TABLE reports ADD COLUMN maturity_level INTEGER NOT NULL DEFAULT 1"))
            if "content_hash" not in existing_rpt:
                conn.execute(text("ALTER TABLE reports ADD COLUMN content_hash VARCHAR(64)"))

    # --- Performance indexes (idempotent) ---
    _index_defs = [
        ("ix_scans_account_id", "scans", "account_id"),
        ("ix_scans_status", "scans", "status"),
        ("ix_scans_cloud_credential_id", "scans", "cloud_credential_id"),
        ("ix_scan_results_scan_id", "scan_results", "scan_id"),
        ("ix_assessment_versions_account_id", "assessment_versions", "account_id"),
        ("ix_evidence_account_id", "evidence", "account_id"),
        ("ix_cloud_credentials_account_id", "cloud_credentials", "account_id"),
        ("ix_remediation_tasks_account_id", "remediation_tasks", "account_id"),
        ("ix_business_processes_account_id", "business_processes", "account_id"),
        ("ix_process_controls_bp_id", "process_controls", "business_process_id"),
        ("ix_evidence_sha256", "evidence", "sha256"),
        ("ix_evidence_deleted_at", "evidence", "deleted_at"),
        ("ix_evidence_links_entity", "evidence_links", "entity_type, entity_id"),
        ("ix_evidence_links_evidence_id", "evidence_links", "evidence_id"),
        ("ix_aqc_question_id", "assessment_question_controls", "question_id"),
        ("ix_aqc_control_id", "assessment_question_controls", "control_id"),
        ("ix_audit_log_account_occurred", "audit_log", "account_id, occurred_at"),
        ("ix_audit_log_entity", "audit_log", "entity_type, entity_id"),
        ("ix_audit_log_correlation", "audit_log", "correlation_id"),
        ("ix_audit_log_event_type", "audit_log", "event_type"),
        ("ix_remediation_plans_account_id", "remediation_plans", "account_id"),
        ("ix_remediation_tasks_plan_id", "remediation_tasks", "plan_id"),
        ("ix_plan_milestones_plan_id", "remediation_plan_milestones", "plan_id"),
        ("ix_plan_links_plan_id", "remediation_plan_links", "plan_id"),
        ("ix_pending_people_tasks_account_id", "pending_people_task_instantiations", "account_id"),
        ("ix_people_tasks_account_id", "people_tasks", "account_id"),
        ("ix_people_tasks_next_due", "people_tasks", "next_due_date"),
        ("ix_people_tasks_subsection", "people_tasks", "article_21_subsection"),
        ("ix_people_tasks_isms_domain", "people_tasks", "isms_domain"),
        ("ix_ptc_task_id", "people_task_completions", "people_task_id"),
        ("ix_ptc_user_id", "people_task_completions", "user_id"),
        ("ix_reports_account_id", "reports", "account_id"),
        ("ix_reports_generated_at", "reports", "generated_at"),
    ]
    for idx_name, tbl, col in _index_defs:
        if tbl in inspector.get_table_names():
            existing_indexes = {idx["name"] for idx in inspector.get_indexes(tbl)}
            if idx_name not in existing_indexes:
                try:
                    with eng.begin() as conn:
                        conn.execute(text(f"CREATE INDEX {idx_name} ON {tbl} ({col})"))
                except Exception:
                    pass  # Index may already exist under a different name


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
