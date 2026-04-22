import enum
import uuid
from datetime import date, datetime, timezone

from sqlalchemy import Boolean, Date, DateTime, Enum, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


class UserRole(str, enum.Enum):
    owner = "owner"
    admin = "admin"
    member = "member"
    auditor_read = "auditor_read"


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _new_uuid() -> str:
    return str(uuid.uuid4())


class Account(Base):
    __tablename__ = "accounts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_uuid)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    api_key_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    country: Mapped[str | None] = mapped_column(String(2), nullable=True)  # ISO 3166-1 alpha-2
    language: Mapped[str | None] = mapped_column(String(5), nullable=True, default="en")  # ISO 639-1
    country_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("countries.id"), nullable=True)
    entity_tier_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("entity_tiers.id"), nullable=True)
    scoring_config: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON: {"technical_weight": 0.6, ...}
    email_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    connected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    aws_accounts: Mapped[list["AwsAccount"]] = relationship(back_populates="account", cascade="all, delete-orphan")
    scans: Mapped[list["Scan"]] = relationship(back_populates="account", cascade="all, delete-orphan")
    assessments: Mapped[list["Assessment"]] = relationship(back_populates="account", cascade="all, delete-orphan")
    evidence_files: Mapped[list["Evidence"]] = relationship(back_populates="account", cascade="all, delete-orphan")
    users: Mapped[list["User"]] = relationship(back_populates="account", cascade="all, delete-orphan")


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_uuid)
    account_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)  # null for pending invites
    role: Mapped[str] = mapped_column(String(20), default=UserRole.member.value, nullable=False)
    email_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    email_verification_token: Mapped[str | None] = mapped_column(String(64), nullable=True)
    email_verification_expires: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    invite_token: Mapped[str | None] = mapped_column(String(64), nullable=True, unique=True)
    invite_expires: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    invite_accepted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    password_reset_token: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    password_reset_expires: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    failed_login_attempts: Mapped[int] = mapped_column(Integer, default=0)
    locked_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)

    account: Mapped["Account"] = relationship(back_populates="users")


class CloudCredential(Base):
    __tablename__ = "cloud_credentials"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_uuid)
    account_id: Mapped[str] = mapped_column(String(36), ForeignKey("accounts.id"), nullable=False, index=True)
    provider: Mapped[str] = mapped_column(String(20), nullable=False)  # "aws" | "azure"
    alias: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    added_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    # AWS fields (encrypted)
    aws_access_key_id: Mapped[str | None] = mapped_column(String(512), nullable=True)
    aws_secret_access_key: Mapped[str | None] = mapped_column(String(512), nullable=True)
    aws_session_token: Mapped[str | None] = mapped_column(Text, nullable=True)
    aws_region: Mapped[str | None] = mapped_column(String(50), nullable=True)
    aws_account_id: Mapped[str | None] = mapped_column(String(20), nullable=True)

    # AWS cross-account role fields (new secure approach)
    aws_role_arn: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    aws_external_id: Mapped[str | None] = mapped_column(String(512), nullable=True)  # encrypted
    aws_connection_type: Mapped[str] = mapped_column(String(20), default="keys")  # "keys" | "role"

    # Azure fields (encrypted)
    azure_tenant_id: Mapped[str | None] = mapped_column(String(512), nullable=True)
    azure_client_id: Mapped[str | None] = mapped_column(String(512), nullable=True)
    azure_client_secret: Mapped[str | None] = mapped_column(String(512), nullable=True)
    azure_subscription_id: Mapped[str | None] = mapped_column(String(512), nullable=True)
    azure_connection_type: Mapped[str] = mapped_column(String(20), default="client_secret")  # "client_secret" | "oauth"

    account: Mapped["Account"] = relationship()
    scans: Mapped[list["Scan"]] = relationship(
        back_populates="cloud_credential",
        foreign_keys="[Scan.cloud_credential_id]",
    )


class AwsAccount(Base):
    __tablename__ = "aws_accounts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_uuid)
    account_id: Mapped[str] = mapped_column(String(36), ForeignKey("accounts.id"), nullable=False)
    alias: Mapped[str] = mapped_column(String(255), nullable=False)
    aws_access_key_id: Mapped[str] = mapped_column(String(512), nullable=False)
    aws_secret_access_key: Mapped[str] = mapped_column(String(512), nullable=False)
    aws_session_token: Mapped[str | None] = mapped_column(Text, nullable=True)
    aws_region: Mapped[str] = mapped_column(String(50), default="eu-west-1")
    aws_account_id: Mapped[str] = mapped_column(String(20), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    added_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    account: Mapped["Account"] = relationship(back_populates="aws_accounts")
    scans: Mapped[list["Scan"]] = relationship(back_populates="aws_account")


class Scan(Base):
    __tablename__ = "scans"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_uuid)
    account_id: Mapped[str] = mapped_column(String(36), ForeignKey("accounts.id"), nullable=False, index=True)
    aws_account_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("aws_accounts.id"), nullable=True)
    cloud_credential_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("cloud_credentials.id"), nullable=True, index=True)
    provider: Mapped[str] = mapped_column(String(20), default="aws")  # "aws" | "azure"
    status: Mapped[str] = mapped_column(
        Enum("queued", "running", "complete", "error", name="scan_status"),
        default="queued",
        index=True,
    )
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    overall_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    total_checks: Mapped[int] = mapped_column(Integer, default=0)
    passed: Mapped[int] = mapped_column(Integer, default=0)
    failed: Mapped[int] = mapped_column(Integer, default=0)
    critical_count: Mapped[int] = mapped_column(Integer, default=0)
    high_count: Mapped[int] = mapped_column(Integer, default=0)
    medium_count: Mapped[int] = mapped_column(Integer, default=0)
    low_count: Mapped[int] = mapped_column(Integer, default=0)

    account: Mapped["Account"] = relationship(back_populates="scans")
    aws_account: Mapped["AwsAccount | None"] = relationship(back_populates="scans")
    cloud_credential: Mapped["CloudCredential | None"] = relationship(
        back_populates="scans",
        foreign_keys=[cloud_credential_id],
    )
    results: Mapped[list["ScanResult"]] = relationship(back_populates="scan", cascade="all, delete-orphan")


class ScanResult(Base):
    __tablename__ = "scan_results"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_uuid)
    scan_id: Mapped[str] = mapped_column(String(36), ForeignKey("scans.id"), nullable=False, index=True)
    check_id: Mapped[str] = mapped_column(String(100), nullable=False)
    nis2_article: Mapped[str] = mapped_column(String(50), nullable=False)
    nis2_requirement: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(
        Enum("pass", "fail", "warn", "info", name="check_status"),
        nullable=False,
    )
    severity: Mapped[str] = mapped_column(String(20), nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    remediation: Mapped[str] = mapped_column(Text, default="")
    remediation_steps: Mapped[str] = mapped_column(Text, default="")  # JSON list
    resource: Mapped[str] = mapped_column(String(500), default="")

    scan: Mapped["Scan"] = relationship(back_populates="results")


class Assessment(Base):
    __tablename__ = "assessments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_uuid)
    account_id: Mapped[str] = mapped_column(String(36), ForeignKey("accounts.id"), nullable=False)
    submitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    human_score: Mapped[float] = mapped_column(Float, nullable=False)
    responses: Mapped[str] = mapped_column(Text, nullable=False)  # JSON string

    account: Mapped["Account"] = relationship(back_populates="assessments")


class AssessmentVersion(Base):
    __tablename__ = "assessment_versions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_uuid)
    account_id: Mapped[str] = mapped_column(String(36), ForeignKey("accounts.id"), nullable=False, index=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    submitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    overall_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    status: Mapped[str] = mapped_column(
        Enum("draft", "submitted", name="assessment_version_status"),
        default="draft",
    )

    account: Mapped["Account"] = relationship()
    responses: Mapped[list["AssessmentResponse"]] = relationship(
        back_populates="assessment_version", cascade="all, delete-orphan"
    )


class AssessmentResponse(Base):
    __tablename__ = "assessment_responses"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_uuid)
    assessment_version_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("assessment_versions.id"), nullable=False
    )
    question_id: Mapped[str] = mapped_column(String(50), nullable=False)
    maturity_level: Mapped[int | None] = mapped_column(Integer, nullable=True)  # 0-4 or null for N/A
    notes: Mapped[str] = mapped_column(Text, default="")
    evidence_refs: Mapped[str] = mapped_column(Text, default="[]")  # JSON array
    answered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    assessment_version: Mapped["AssessmentVersion"] = relationship(back_populates="responses")


class Evidence(Base):
    __tablename__ = "evidence"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_uuid)
    account_id: Mapped[str] = mapped_column(String(36), ForeignKey("accounts.id"), nullable=False, index=True)
    control_id: Mapped[str | None] = mapped_column(String(100), nullable=True)  # legacy, nullable for new uploads
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    stored_filename: Mapped[str] = mapped_column(String(500), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)
    content_type: Mapped[str] = mapped_column(String(100), nullable=False)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    uploaded_by: Mapped[str] = mapped_column(String(255), nullable=False)

    # Phase 2 additions
    s3_key: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    sha256: Mapped[str | None] = mapped_column(String(64), nullable=True)
    description: Mapped[str] = mapped_column(Text, default="")
    tags: Mapped[str] = mapped_column(Text, default="[]")  # JSON array
    retention_until: Mapped[datetime | None] = mapped_column(Date, nullable=True)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    uploaded_by_user_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)

    account: Mapped["Account"] = relationship(back_populates="evidence_files")
    links: Mapped[list["EvidenceLink"]] = relationship(back_populates="evidence", cascade="all, delete-orphan")


class RemediationPlan(Base):
    """Narrative treatment plan wrapping one or more remediation tasks."""
    __tablename__ = "remediation_plans"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_uuid)
    account_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="")
    treatment_type: Mapped[str] = mapped_column(String(20), nullable=False, default="mitigate")  # mitigate|transfer|avoid|accept
    status: Mapped[str] = mapped_column(
        String(30), default="draft",  # draft|pending_approval|approved|in_progress|completed|rejected
    )
    target_date: Mapped[datetime | None] = mapped_column(Date, nullable=True)
    created_by_user_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    approved_by_user_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    rejected_by_user_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    rejected_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    rejection_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)

    account: Mapped["Account"] = relationship()
    milestones: Mapped[list["RemediationPlanMilestone"]] = relationship(
        back_populates="plan", cascade="all, delete-orphan"
    )
    links: Mapped[list["RemediationPlanLink"]] = relationship(
        back_populates="plan", cascade="all, delete-orphan"
    )
    tasks: Mapped[list["RemediationTask"]] = relationship(back_populates="plan")


class RemediationPlanMilestone(Base):
    """Progress checkpoint within a remediation plan."""
    __tablename__ = "remediation_plan_milestones"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_uuid)
    plan_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("remediation_plans.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="")
    target_date: Mapped[datetime | None] = mapped_column(Date, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    display_order: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    plan: Mapped["RemediationPlan"] = relationship(back_populates="milestones")


class RemediationPlanLink(Base):
    """Connects a plan to controls, questions, or processes."""
    __tablename__ = "remediation_plan_links"
    __table_args__ = (
        UniqueConstraint("plan_id", "entity_type", "entity_id", name="uq_plan_links_plan_entity"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_uuid)
    plan_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("remediation_plans.id", ondelete="CASCADE"), nullable=False, index=True
    )
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False)  # control|question|process
    entity_id: Mapped[str] = mapped_column(String(100), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    plan: Mapped["RemediationPlan"] = relationship(back_populates="links")


class RemediationTask(Base):
    __tablename__ = "remediation_tasks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_uuid)
    account_id: Mapped[str] = mapped_column(String(36), ForeignKey("accounts.id"), nullable=False, index=True)
    question_id: Mapped[str] = mapped_column(String(50), nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(
        Enum("open", "in_progress", "completed", "dismissed", name="remediation_status"),
        default="open",
    )
    priority: Mapped[str] = mapped_column(String(20), default="medium")
    assigned_to: Mapped[str | None] = mapped_column(String(255), nullable=True)
    due_date: Mapped[datetime | None] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Phase 3 additions
    plan_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("remediation_plans.id", ondelete="SET NULL"), nullable=True, index=True
    )
    related_control_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    related_assessment_answer_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    severity: Mapped[str] = mapped_column(String(20), default="medium")
    auto_generated: Mapped[bool] = mapped_column(Boolean, default=False)
    closure_evidence_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("evidence.id", ondelete="SET NULL"), nullable=True
    )
    closure_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    closed_by_user_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    dismissed_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    dismissed_by_user_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    dismissed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    original_due_date: Mapped[datetime | None] = mapped_column(Date, nullable=True)
    reschedule_count: Mapped[int] = mapped_column(Integer, default=0)

    account: Mapped["Account"] = relationship()
    plan: Mapped["RemediationPlan | None"] = relationship(back_populates="tasks")


# --- Country-specific NIS2 tables ---


class Country(Base):
    __tablename__ = "countries"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_uuid)
    code: Mapped[str] = mapped_column(String(2), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    name_local: Mapped[str | None] = mapped_column(String(100), nullable=True)
    transposition_status: Mapped[str] = mapped_column(String(20), nullable=False, default="unknown")
    transposition_law_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    transposition_law_reference: Mapped[str | None] = mapped_column(String(255), nullable=True)
    transposition_law_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    date_published: Mapped[str | None] = mapped_column(Date, nullable=True)
    date_effective: Mapped[str | None] = mapped_column(Date, nullable=True)
    competent_authority_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    competent_authority_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    csirt_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    csirt_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    research_confidence: Mapped[str | None] = mapped_column(String(10), nullable=True)
    research_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)

    tiers: Mapped[list["EntityTier"]] = relationship(back_populates="country", cascade="all, delete-orphan")
    controls: Mapped[list["CountryControl"]] = relationship(back_populates="country", cascade="all, delete-orphan")
    deadlines: Mapped[list["CountryDeadline"]] = relationship(back_populates="country", cascade="all, delete-orphan")
    assessment_questions: Mapped[list["CountryAssessmentQuestion"]] = relationship(
        back_populates="country", cascade="all, delete-orphan"
    )


class EntityTier(Base):
    __tablename__ = "entity_tiers"
    __table_args__ = (UniqueConstraint("country_id", "tier_key", name="uq_entity_tiers_country_tier"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_uuid)
    country_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("countries.id", ondelete="CASCADE"), nullable=False, index=True
    )
    tier_key: Mapped[str] = mapped_column(String(50), nullable=False)
    local_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    sectors: Mapped[str] = mapped_column(Text, default="[]")  # JSON array
    size_thresholds: Mapped[str] = mapped_column(Text, default="{}")  # JSON object
    obligations: Mapped[str] = mapped_column(Text, default="{}")  # JSON object
    penalties: Mapped[str] = mapped_column(Text, default="{}")  # JSON object
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)

    country: Mapped["Country"] = relationship(back_populates="tiers")


class CountryControl(Base):
    __tablename__ = "country_controls"
    __table_args__ = (UniqueConstraint("country_id", "control_id", name="uq_country_controls_country_control"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_uuid)
    country_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("countries.id", ondelete="CASCADE"), nullable=False, index=True
    )
    control_id: Mapped[str] = mapped_column(String(50), nullable=False)
    eu_article: Mapped[str | None] = mapped_column(String(20), nullable=True)
    national_legal_reference: Mapped[str | None] = mapped_column(String(255), nullable=True)
    national_specification: Mapped[str | None] = mapped_column(Text, nullable=True)
    goes_beyond_eu: Mapped[bool] = mapped_column(Boolean, default=False)
    applies_to_tiers: Mapped[str] = mapped_column(Text, default='["essential", "important"]')  # JSON array
    additional_requirements: Mapped[str] = mapped_column(Text, default="[]")  # JSON array
    is_mandatory: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)

    country: Mapped["Country"] = relationship(back_populates="controls")


class CountryDeadline(Base):
    __tablename__ = "country_deadlines"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_uuid)
    country_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("countries.id", ondelete="CASCADE"), nullable=False, index=True
    )
    deadline_date: Mapped[str] = mapped_column(Date, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    applies_to_tiers: Mapped[str] = mapped_column(Text, default="[]")  # JSON array
    legal_reference: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    country: Mapped["Country"] = relationship(back_populates="deadlines")


class CountryAssessmentQuestion(Base):
    __tablename__ = "country_assessment_questions"
    __table_args__ = (
        UniqueConstraint("country_id", "base_question_id", name="uq_country_aq_country_question"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_uuid)
    country_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("countries.id", ondelete="CASCADE"), nullable=False, index=True
    )
    base_question_id: Mapped[str | None] = mapped_column(String(50), nullable=True)
    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    help_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    eu_article: Mapped[str | None] = mapped_column(String(20), nullable=True)
    national_legal_reference: Mapped[str | None] = mapped_column(String(255), nullable=True)
    applies_to_tiers: Mapped[str] = mapped_column(Text, default='["essential", "important"]')  # JSON array
    domain: Mapped[str | None] = mapped_column(String(100), nullable=True)
    weight: Mapped[float] = mapped_column(Float, default=1.0)
    is_additional: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)

    country: Mapped["Country"] = relationship(back_populates="assessment_questions")


# --- Per-account control state ---


class BaseControl(Base):
    __tablename__ = "base_controls"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_uuid)
    control_id: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    article: Mapped[str] = mapped_column(String(50), nullable=False)
    article_area: Mapped[str] = mapped_column(String(100), nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    severity: Mapped[str] = mapped_column(String(20), nullable=False)
    is_people_control: Mapped[bool] = mapped_column(Boolean, default=False)
    display_order: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class AccountControl(Base):
    __tablename__ = "account_controls"
    __table_args__ = (
        UniqueConstraint("account_id", "control_id", name="uq_account_controls_account_control"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_uuid)
    account_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    control_id: Mapped[str] = mapped_column(String(100), nullable=False)  # e.g. "ctrl-001"
    status: Mapped[str] = mapped_column(String(20), default="Not Started")
    owner: Mapped[str] = mapped_column(String(255), default="")
    due_date: Mapped[str | None] = mapped_column(Date, nullable=True)
    notes: Mapped[str] = mapped_column(Text, default="")
    is_country_specific: Mapped[bool] = mapped_column(Boolean, default=False)
    last_updated: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)

    account: Mapped["Account"] = relationship()


class ControlCampaign(Base):
    __tablename__ = "control_campaigns"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_uuid)
    account_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    control_id: Mapped[str] = mapped_column(String(100), nullable=False)
    control_name: Mapped[str] = mapped_column(String(500), nullable=False)
    task_type: Mapped[str] = mapped_column(String(20), nullable=False)  # acknowledge | quiz
    deadline: Mapped[str] = mapped_column(String(20), nullable=False)
    policy_content: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    account: Mapped["Account"] = relationship()
    tasks: Mapped[list["CampaignTask"]] = relationship(
        back_populates="campaign", cascade="all, delete-orphan"
    )


class CampaignTask(Base):
    __tablename__ = "campaign_tasks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_uuid)
    campaign_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("control_campaigns.id", ondelete="CASCADE"), nullable=False, index=True
    )
    control_id: Mapped[str] = mapped_column(String(100), nullable=False)
    employee_name: Mapped[str] = mapped_column(String(255), nullable=False)
    employee_email: Mapped[str] = mapped_column(String(255), nullable=False)
    department: Mapped[str] = mapped_column(String(255), default="")
    task_type: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="pending")
    sent_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    completed_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    deadline: Mapped[str] = mapped_column(String(20), nullable=False)
    score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    completion_token: Mapped[str | None] = mapped_column(String(64), nullable=True, unique=True)

    campaign: Mapped["ControlCampaign"] = relationship(back_populates="tasks")


class BusinessProcess(Base):
    """A critical business process scoped by the account for NIS2 compliance."""
    __tablename__ = "business_processes"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_uuid)
    account_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="")
    is_critical: Mapped[bool] = mapped_column(Boolean, default=True)
    owner: Mapped[str] = mapped_column(String(255), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)

    account: Mapped["Account"] = relationship()
    process_controls: Mapped[list["ProcessControl"]] = relationship(
        back_populates="business_process", cascade="all, delete-orphan"
    )


class ProcessControl(Base):
    """Many-to-many link between business processes and controls with applicability metadata."""
    __tablename__ = "process_controls"
    __table_args__ = (
        UniqueConstraint("business_process_id", "control_id", name="uq_process_controls_bp_ctrl"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_uuid)
    business_process_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("business_processes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    control_id: Mapped[str] = mapped_column(String(100), nullable=False)  # e.g. "ctrl-001"
    applicable: Mapped[bool] = mapped_column(Boolean, default=True)
    justification: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    business_process: Mapped["BusinessProcess"] = relationship(back_populates="process_controls")


class OAuthState(Base):
    """Temporary state for OAuth2 flows (e.g. Azure admin consent)."""
    __tablename__ = "oauth_states"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_uuid)
    account_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    state_token: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    provider: Mapped[str] = mapped_column(String(20), nullable=False)  # "azure"
    alias: Mapped[str] = mapped_column(String(255), nullable=False)
    subscription_id: Mapped[str | None] = mapped_column(String(512), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


# --- Phase 2: Evidence links, assessment-control mapping, audit log ---


class EvidenceLink(Base):
    """Polymorphic link between an evidence file and any compliance entity."""
    __tablename__ = "evidence_links"
    __table_args__ = (
        UniqueConstraint("evidence_id", "entity_type", "entity_id", name="uq_evidence_links_active"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_uuid)
    evidence_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("evidence.id", ondelete="CASCADE"), nullable=False, index=True
    )
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False)  # assessment_answer, control, remediation_task, people_task, process
    entity_id: Mapped[str] = mapped_column(String(100), nullable=False)
    link_type: Mapped[str] = mapped_column(String(20), default="primary")  # primary, supporting, closure, working, scope
    linked_by_user_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    linked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    unlinked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    evidence: Mapped["Evidence"] = relationship(back_populates="links")


class AssessmentQuestionControl(Base):
    """Mapping between assessment questions and controls with weight."""
    __tablename__ = "assessment_question_controls"
    __table_args__ = (
        UniqueConstraint("question_id", "control_id", name="uq_aqc_question_control"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_uuid)
    question_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    control_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    weight: Mapped[float] = mapped_column(Float, default=1.0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class AuditLog(Base):
    """Tamper-evident audit trail for all compliance-relevant actions."""
    __tablename__ = "audit_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    account_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("accounts.id"), nullable=True, index=True)
    event_type: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    event_category: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    actor_user_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    actor_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    actor_ip: Mapped[str | None] = mapped_column(String(45), nullable=True)
    entity_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    entity_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    entity_label: Mapped[str | None] = mapped_column(String(300), nullable=True)
    correlation_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    before_state: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON
    after_state: Mapped[str | None] = mapped_column(Text, nullable=True)   # JSON
    change_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_material: Mapped[bool] = mapped_column(Boolean, default=False)
    metadata_json: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, index=True)
    hash: Mapped[str] = mapped_column(String(64), nullable=False)
    prev_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)


class PendingPeopleTaskInstantiation(Base):
    """Queue for Phase 4: people-control task instantiation from closed remediation tasks."""
    __tablename__ = "pending_people_task_instantiations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_uuid)
    account_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    control_id: Mapped[str] = mapped_column(String(100), nullable=False)
    task_type: Mapped[str] = mapped_column(String(20), nullable=False, default="acknowledge")  # acknowledge|quiz
    source_plan_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("remediation_plans.id"), nullable=True)
    source_task_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("remediation_tasks.id"), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="pending")  # pending|instantiated|cancelled
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    instantiated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


# ---------------------------------------------------------------------------
# Phase 4: People Tasks — Continuous Compliance (embedded mini-ISMS)
# ---------------------------------------------------------------------------


class PeopleTask(Base):
    """Recurring or one-off continuous compliance task (embedded mini-ISMS)."""
    __tablename__ = "people_tasks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_uuid)
    account_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="")
    task_type: Mapped[str] = mapped_column(String(30), nullable=False)
    # attestation | process_check | evidence_submission | policy_ack | training
    pdca_phase: Mapped[str] = mapped_column(String(10), nullable=False)  # plan | do | check | act
    article_21_subsection: Mapped[str] = mapped_column(String(5), nullable=False)  # a-j
    frequency: Mapped[str] = mapped_column(String(20), nullable=False)
    # one_off | monthly | quarterly | annual
    next_due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    assignee_user_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("users.id"), nullable=True
    )
    assignee_role: Mapped[str | None] = mapped_column(String(50), nullable=True)
    related_control_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    related_process_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("business_processes.id", ondelete="SET NULL"), nullable=True
    )
    related_plan_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("remediation_plans.id", ondelete="SET NULL"), nullable=True
    )
    requires_evidence: Mapped[bool] = mapped_column(Boolean, default=False)
    attestation_statement: Mapped[str | None] = mapped_column(Text, nullable=True)
    baseline_template_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    isms_domain: Mapped[str | None] = mapped_column(String(50), nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)

    account: Mapped["Account"] = relationship()
    completions: Mapped[list["PeopleTaskCompletion"]] = relationship(
        back_populates="people_task", cascade="all, delete-orphan"
    )


class PeopleTaskCompletion(Base):
    """One completion record per user per period for a people task."""
    __tablename__ = "people_task_completions"
    __table_args__ = (
        UniqueConstraint("people_task_id", "user_id", "period_key", name="uq_ptc_task_user_period"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_uuid)
    people_task_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("people_tasks.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id"), nullable=False, index=True
    )
    period_key: Mapped[str] = mapped_column(String(20), nullable=False)
    attested_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    attestation_response: Mapped[str | None] = mapped_column(Text, nullable=True)
    evidence_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("evidence.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    people_task: Mapped["PeopleTask"] = relationship(back_populates="completions")
