import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, Date, DateTime, Enum, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _new_uuid() -> str:
    return str(uuid.uuid4())


class Account(Base):
    __tablename__ = "accounts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_uuid)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    api_key_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    failed_login_attempts: Mapped[int] = mapped_column(Integer, default=0)
    locked_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    country: Mapped[str | None] = mapped_column(String(2), nullable=True)  # ISO 3166-1 alpha-2
    language: Mapped[str | None] = mapped_column(String(5), nullable=True, default="en")  # ISO 639-1
    country_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("countries.id"), nullable=True)
    entity_tier_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("entity_tiers.id"), nullable=True)
    scoring_config: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON: {"technical_weight": 0.6, ...}
    connected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    aws_accounts: Mapped[list["AwsAccount"]] = relationship(back_populates="account", cascade="all, delete-orphan")
    scans: Mapped[list["Scan"]] = relationship(back_populates="account", cascade="all, delete-orphan")
    assessments: Mapped[list["Assessment"]] = relationship(back_populates="account", cascade="all, delete-orphan")
    evidence_files: Mapped[list["Evidence"]] = relationship(back_populates="account", cascade="all, delete-orphan")


class CloudCredential(Base):
    __tablename__ = "cloud_credentials"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_uuid)
    account_id: Mapped[str] = mapped_column(String(36), ForeignKey("accounts.id"), nullable=False)
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

    # Azure fields (encrypted)
    azure_tenant_id: Mapped[str | None] = mapped_column(String(512), nullable=True)
    azure_client_id: Mapped[str | None] = mapped_column(String(512), nullable=True)
    azure_client_secret: Mapped[str | None] = mapped_column(String(512), nullable=True)
    azure_subscription_id: Mapped[str | None] = mapped_column(String(512), nullable=True)

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
    account_id: Mapped[str] = mapped_column(String(36), ForeignKey("accounts.id"), nullable=False)
    aws_account_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("aws_accounts.id"), nullable=True)
    cloud_credential_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("cloud_credentials.id"), nullable=True)
    provider: Mapped[str] = mapped_column(String(20), default="aws")  # "aws" | "azure"
    status: Mapped[str] = mapped_column(
        Enum("queued", "running", "complete", "error", name="scan_status"),
        default="queued",
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
    scan_id: Mapped[str] = mapped_column(String(36), ForeignKey("scans.id"), nullable=False)
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
    account_id: Mapped[str] = mapped_column(String(36), ForeignKey("accounts.id"), nullable=False)
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
    account_id: Mapped[str] = mapped_column(String(36), ForeignKey("accounts.id"), nullable=False)
    control_id: Mapped[str] = mapped_column(String(100), nullable=False)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    stored_filename: Mapped[str] = mapped_column(String(500), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)
    content_type: Mapped[str] = mapped_column(String(100), nullable=False)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    uploaded_by: Mapped[str] = mapped_column(String(255), nullable=False)

    account: Mapped["Account"] = relationship(back_populates="evidence_files")


class RemediationTask(Base):
    __tablename__ = "remediation_tasks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_uuid)
    account_id: Mapped[str] = mapped_column(String(36), ForeignKey("accounts.id"), nullable=False)
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

    account: Mapped["Account"] = relationship()


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
