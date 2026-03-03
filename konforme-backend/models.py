import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, Date, DateTime, Enum, Float, ForeignKey, Integer, String, Text
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
    connected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    aws_accounts: Mapped[list["AwsAccount"]] = relationship(back_populates="account", cascade="all, delete-orphan")
    scans: Mapped[list["Scan"]] = relationship(back_populates="account", cascade="all, delete-orphan")
    assessments: Mapped[list["Assessment"]] = relationship(back_populates="account", cascade="all, delete-orphan")


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
