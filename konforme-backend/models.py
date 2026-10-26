"""Konforme data model, stored in DynamoDB (see store.py for the key layout).

Field names match the former PostgreSQL columns. Each class declares:
    __partition__  (prefix, field) -> PK; field None = one shared reference partition
    __sort__       fields after the model name in SK (default: id); also enforces
                   uniqueness for composite keys, like the old UNIQUE constraints
    __lookups__    GSI attribute -> field, for lookups without knowing the partition
    __unique__     fields that must be unique across the table (guard items)
    __onupdate__   timestamp fields refreshed whenever the object changes
"""

import enum
import uuid
from dataclasses import dataclass, field
from datetime import date, datetime, timezone

from store import next_sequence, session_of


class UserRole(str, enum.Enum):
    owner = "owner"
    admin = "admin"
    member = "member"
    auditor_read = "auditor_read"


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _new_uuid() -> str:
    return str(uuid.uuid4())


def _next_audit_id() -> int:
    return next_sequence("AuditLog")


model = dataclass(kw_only=True, eq=False)



@model
class Account:
    __partition__ = ("Account", "id")
    __sort__ = ()
    __lookups__ = {"lk_email": "email"}
    __unique__ = ("email",)

    id: str | None = field(default_factory=_new_uuid)
    name: str | None = None
    email: str | None = None
    api_key_hash: str | None = None
    is_active: bool | None = True
    country: str | None = None
    language: str | None = "en"
    country_id: str | None = None
    entity_tier_id: str | None = None
    scoring_config: str | None = None
    email_verified: bool | None = False
    connected_at: datetime | None = field(default_factory=_utcnow)

    @property
    def aws_accounts(self) -> list["AwsAccount"]:
        return session_of(self).list(AwsAccount, self.id)


@model
class User:
    __partition__ = ("Account", "account_id")
    __lookups__ = {"lk_email": "email", "lk_token": "invite_token", "lk_verify": "email_verification_token", "lk_reset": "password_reset_token"}
    __unique__ = ("email",)
    __onupdate__ = ("updated_at",)

    id: str | None = field(default_factory=_new_uuid)
    account_id: str | None = None
    name: str | None = None
    email: str | None = None
    password_hash: str | None = None
    role: str | None = "member"
    email_verified: bool | None = False
    email_verification_token: str | None = None
    email_verification_expires: datetime | None = None
    invite_token: str | None = None
    invite_expires: datetime | None = None
    invite_accepted_at: datetime | None = None
    password_reset_token: str | None = None
    password_reset_expires: datetime | None = None
    is_active: bool | None = True
    failed_login_attempts: int | None = 0
    locked_until: datetime | None = None
    created_at: datetime | None = field(default_factory=_utcnow)
    updated_at: datetime | None = field(default_factory=_utcnow)


@model
class CloudCredential:
    __partition__ = ("Account", "account_id")

    id: str | None = field(default_factory=_new_uuid)
    account_id: str | None = None
    provider: str | None = None
    alias: str | None = None
    is_active: bool | None = True
    added_at: datetime | None = field(default_factory=_utcnow)
    aws_access_key_id: str | None = None
    aws_secret_access_key: str | None = None
    aws_session_token: str | None = None
    aws_region: str | None = None
    aws_account_id: str | None = None
    aws_role_arn: str | None = None
    aws_external_id: str | None = None
    aws_connection_type: str | None = "keys"
    azure_tenant_id: str | None = None
    azure_client_id: str | None = None
    azure_client_secret: str | None = None
    azure_subscription_id: str | None = None
    azure_connection_type: str | None = "client_secret"


@model
class AwsAccount:
    __partition__ = ("Account", "account_id")

    id: str | None = field(default_factory=_new_uuid)
    account_id: str | None = None
    alias: str | None = None
    aws_access_key_id: str | None = None
    aws_secret_access_key: str | None = None
    aws_session_token: str | None = None
    aws_region: str | None = "eu-west-1"
    aws_account_id: str | None = None
    is_active: bool | None = True
    added_at: datetime | None = field(default_factory=_utcnow)


@model
class Scan:
    __partition__ = ("Account", "account_id")

    id: str | None = field(default_factory=_new_uuid)
    account_id: str | None = None
    aws_account_id: str | None = None
    cloud_credential_id: str | None = None
    provider: str | None = "aws"
    status: str | None = "queued"
    started_at: datetime | None = field(default_factory=_utcnow)
    completed_at: datetime | None = None
    overall_score: float | None = None
    total_checks: int | None = 0
    passed: int | None = 0
    failed: int | None = 0
    critical_count: int | None = 0
    high_count: int | None = 0
    medium_count: int | None = 0
    low_count: int | None = 0

    @property
    def aws_account(self) -> "AwsAccount | None":
        if not self.aws_account_id:
            return None
        return session_of(self).get_by_key(AwsAccount, self.account_id, id=self.aws_account_id)


@model
class ScanResult:
    __partition__ = ("Scan", "scan_id")

    id: str | None = field(default_factory=_new_uuid)
    scan_id: str | None = None
    check_id: str | None = None
    nis2_article: str | None = None
    nis2_requirement: str | None = None
    status: str | None = None
    severity: str | None = None
    title: str | None = None
    message: str | None = None
    remediation: str | None = ""
    remediation_steps: str | None = ""
    resource: str | None = ""


@model
class Assessment:
    __partition__ = ("Account", "account_id")

    id: str | None = field(default_factory=_new_uuid)
    account_id: str | None = None
    submitted_at: datetime | None = field(default_factory=_utcnow)
    human_score: float | None = None
    responses: str | None = None


@model
class AssessmentVersion:
    __partition__ = ("Account", "account_id")

    id: str | None = field(default_factory=_new_uuid)
    account_id: str | None = None
    version: int | None = 1
    submitted_at: datetime | None = field(default_factory=_utcnow)
    overall_score: float | None = None
    status: str | None = "draft"

    @property
    def responses(self) -> list["AssessmentResponse"]:
        return session_of(self).list(AssessmentResponse, self.id)


@model
class AssessmentResponse:
    __partition__ = ("AssessmentVersion", "assessment_version_id")

    id: str | None = field(default_factory=_new_uuid)
    assessment_version_id: str | None = None
    question_id: str | None = None
    maturity_level: int | None = None
    notes: str | None = ""
    evidence_refs: str | None = "[]"
    answered_at: datetime | None = field(default_factory=_utcnow)


@model
class Evidence:
    __partition__ = ("Account", "account_id")

    id: str | None = field(default_factory=_new_uuid)
    account_id: str | None = None
    control_id: str | None = None
    filename: str | None = None
    stored_filename: str | None = None
    file_size: int | None = None
    content_type: str | None = None
    uploaded_at: datetime | None = field(default_factory=_utcnow)
    uploaded_by: str | None = None
    s3_key: str | None = None
    sha256: str | None = None
    description: str | None = ""
    tags: str | None = "[]"
    retention_until: date | None = None
    deleted_at: datetime | None = None
    uploaded_by_user_id: str | None = None

    @property
    def links(self) -> list["EvidenceLink"]:
        return [lnk for lnk in session_of(self).list(EvidenceLink, self.account_id) if lnk.evidence_id == self.id]


@model
class RemediationPlan:
    """Narrative treatment plan wrapping one or more remediation tasks."""

    __partition__ = ("Account", "account_id")
    __onupdate__ = ("updated_at",)

    id: str | None = field(default_factory=_new_uuid)
    account_id: str | None = None
    title: str | None = None
    description: str | None = ""
    treatment_type: str | None = "mitigate"
    status: str | None = "draft"
    target_date: date | None = None
    created_by_user_id: str | None = None
    approved_by_user_id: str | None = None
    approved_at: datetime | None = None
    rejected_by_user_id: str | None = None
    rejected_at: datetime | None = None
    rejection_reason: str | None = None
    created_at: datetime | None = field(default_factory=_utcnow)
    updated_at: datetime | None = field(default_factory=_utcnow)

    @property
    def milestones(self) -> list["RemediationPlanMilestone"]:
        return session_of(self).list(RemediationPlanMilestone, self.id)

    @property
    def links(self) -> list["RemediationPlanLink"]:
        return session_of(self).list(RemediationPlanLink, self.id)

    @property
    def tasks(self) -> list["RemediationTask"]:
        return [t for t in session_of(self).list(RemediationTask, self.account_id) if t.plan_id == self.id]


@model
class RemediationPlanMilestone:
    """Progress checkpoint within a remediation plan."""

    __partition__ = ("RemediationPlan", "plan_id")

    id: str | None = field(default_factory=_new_uuid)
    plan_id: str | None = None
    title: str | None = None
    description: str | None = ""
    target_date: date | None = None
    completed_at: datetime | None = None
    display_order: int | None = 0
    created_at: datetime | None = field(default_factory=_utcnow)


@model
class RemediationPlanLink:
    """Connects a plan to controls, questions, or processes."""

    __partition__ = ("RemediationPlan", "plan_id")
    __sort__ = ("entity_type", "entity_id")

    id: str | None = field(default_factory=_new_uuid)
    plan_id: str | None = None
    entity_type: str | None = None
    entity_id: str | None = None
    created_at: datetime | None = field(default_factory=_utcnow)


@model
class RemediationTask:
    __partition__ = ("Account", "account_id")
    __onupdate__ = ("updated_at",)

    id: str | None = field(default_factory=_new_uuid)
    account_id: str | None = None
    question_id: str | None = None
    title: str | None = None
    description: str | None = ""
    status: str | None = "open"
    priority: str | None = "medium"
    assigned_to: str | None = None
    due_date: date | None = None
    created_at: datetime | None = field(default_factory=_utcnow)
    updated_at: datetime | None = field(default_factory=_utcnow)
    completed_at: datetime | None = None
    plan_id: str | None = None
    related_control_id: str | None = None
    related_assessment_answer_id: str | None = None
    severity: str | None = "medium"
    auto_generated: bool | None = False
    closure_evidence_id: str | None = None
    closure_note: str | None = None
    closed_by_user_id: str | None = None
    dismissed_reason: str | None = None
    dismissed_by_user_id: str | None = None
    dismissed_at: datetime | None = None
    original_due_date: date | None = None
    reschedule_count: int | None = 0


@model
class Country:
    __partition__ = ("Ref", None)
    __sort__ = ("code",)
    __onupdate__ = ("updated_at",)

    id: str | None = field(default_factory=_new_uuid)
    code: str | None = None
    name: str | None = None
    name_local: str | None = None
    transposition_status: str | None = "unknown"
    transposition_law_name: str | None = None
    transposition_law_reference: str | None = None
    transposition_law_url: str | None = None
    date_published: date | None = None
    date_effective: date | None = None
    competent_authority_name: str | None = None
    competent_authority_url: str | None = None
    csirt_name: str | None = None
    csirt_url: str | None = None
    research_confidence: str | None = None
    research_notes: str | None = None
    created_at: datetime | None = field(default_factory=_utcnow)
    updated_at: datetime | None = field(default_factory=_utcnow)

    @property
    def tiers(self) -> list["EntityTier"]:
        return session_of(self).list(EntityTier, self.id)

    @property
    def controls(self) -> list["CountryControl"]:
        return session_of(self).list(CountryControl, self.id)

    @property
    def deadlines(self) -> list["CountryDeadline"]:
        return session_of(self).list(CountryDeadline, self.id)

    @property
    def assessment_questions(self) -> list["CountryAssessmentQuestion"]:
        return session_of(self).list(CountryAssessmentQuestion, self.id)


@model
class EntityTier:
    __partition__ = ("Country", "country_id")
    __sort__ = ("tier_key",)
    __onupdate__ = ("updated_at",)

    id: str | None = field(default_factory=_new_uuid)
    country_id: str | None = None
    tier_key: str | None = None
    local_name: str | None = None
    description: str | None = None
    sectors: str | None = "[]"
    size_thresholds: str | None = "{}"
    obligations: str | None = "{}"
    penalties: str | None = "{}"
    created_at: datetime | None = field(default_factory=_utcnow)
    updated_at: datetime | None = field(default_factory=_utcnow)


@model
class CountryControl:
    __partition__ = ("Country", "country_id")
    __sort__ = ("control_id",)
    __onupdate__ = ("updated_at",)

    id: str | None = field(default_factory=_new_uuid)
    country_id: str | None = None
    control_id: str | None = None
    eu_article: str | None = None
    national_legal_reference: str | None = None
    national_specification: str | None = None
    goes_beyond_eu: bool | None = False
    applies_to_tiers: str | None = '["essential", "important"]'
    additional_requirements: str | None = "[]"
    is_mandatory: bool | None = True
    created_at: datetime | None = field(default_factory=_utcnow)
    updated_at: datetime | None = field(default_factory=_utcnow)


@model
class CountryDeadline:
    __partition__ = ("Country", "country_id")

    id: str | None = field(default_factory=_new_uuid)
    country_id: str | None = None
    deadline_date: date | None = None
    description: str | None = None
    applies_to_tiers: str | None = "[]"
    legal_reference: str | None = None
    created_at: datetime | None = field(default_factory=_utcnow)


@model
class CountryAssessmentQuestion:
    __partition__ = ("Country", "country_id")
    __onupdate__ = ("updated_at",)

    id: str | None = field(default_factory=_new_uuid)
    country_id: str | None = None
    base_question_id: str | None = None
    question_text: str | None = None
    help_text: str | None = None
    eu_article: str | None = None
    national_legal_reference: str | None = None
    applies_to_tiers: str | None = '["essential", "important"]'
    domain: str | None = None
    weight: float | None = 1.0
    is_additional: bool | None = False
    created_at: datetime | None = field(default_factory=_utcnow)
    updated_at: datetime | None = field(default_factory=_utcnow)


@model
class BaseControl:
    __partition__ = ("Ref", None)
    __sort__ = ("control_id",)

    id: str | None = field(default_factory=_new_uuid)
    control_id: str | None = None
    title: str | None = None
    description: str | None = None
    article: str | None = None
    article_area: str | None = None
    category: str | None = None
    severity: str | None = None
    is_people_control: bool | None = False
    display_order: int | None = 0
    created_at: datetime | None = field(default_factory=_utcnow)


@model
class AccountControl:
    __partition__ = ("Account", "account_id")
    __sort__ = ("control_id",)
    __onupdate__ = ("last_updated",)

    id: str | None = field(default_factory=_new_uuid)
    account_id: str | None = None
    control_id: str | None = None
    status: str | None = "Not Started"
    owner: str | None = ""
    due_date: date | None = None
    notes: str | None = ""
    is_country_specific: bool | None = False
    last_updated: datetime | None = field(default_factory=_utcnow)


@model
class ControlCampaign:
    __partition__ = ("Account", "account_id")

    id: str | None = field(default_factory=_new_uuid)
    account_id: str | None = None
    control_id: str | None = None
    control_name: str | None = None
    task_type: str | None = None
    deadline: str | None = None
    policy_content: str | None = None
    created_at: datetime | None = field(default_factory=_utcnow)

    @property
    def tasks(self) -> list["CampaignTask"]:
        return session_of(self).list(CampaignTask, self.id)


@model
class CampaignTask:
    __partition__ = ("ControlCampaign", "campaign_id")
    __lookups__ = {"lk_token": "completion_token"}

    id: str | None = field(default_factory=_new_uuid)
    campaign_id: str | None = None
    control_id: str | None = None
    employee_name: str | None = None
    employee_email: str | None = None
    department: str | None = ""
    task_type: str | None = None
    status: str | None = "pending"
    sent_date: datetime | None = field(default_factory=_utcnow)
    completed_date: datetime | None = None
    deadline: str | None = None
    score: int | None = None
    completion_token: str | None = None


@model
class BusinessProcess:
    """A critical business process scoped by the account for NIS2 compliance."""

    __partition__ = ("Account", "account_id")
    __onupdate__ = ("updated_at",)

    id: str | None = field(default_factory=_new_uuid)
    account_id: str | None = None
    name: str | None = None
    description: str | None = ""
    is_critical: bool | None = True
    owner: str | None = ""
    created_at: datetime | None = field(default_factory=_utcnow)
    updated_at: datetime | None = field(default_factory=_utcnow)

    @property
    def process_controls(self) -> list["ProcessControl"]:
        return session_of(self).list(ProcessControl, self.id)


@model
class ProcessControl:
    """Many-to-many link between business processes and controls with applicability metadata."""

    __partition__ = ("BusinessProcess", "business_process_id")
    __sort__ = ("control_id",)

    id: str | None = field(default_factory=_new_uuid)
    business_process_id: str | None = None
    control_id: str | None = None
    applicable: bool | None = True
    justification: str | None = ""
    created_at: datetime | None = field(default_factory=_utcnow)


@model
class OAuthState:
    """Temporary state for OAuth2 flows (e.g. Azure admin consent)."""

    __partition__ = ("Account", "account_id")
    __lookups__ = {"lk_token": "state_token"}

    id: str | None = field(default_factory=_new_uuid)
    account_id: str | None = None
    state_token: str | None = None
    provider: str | None = None
    alias: str | None = None
    subscription_id: str | None = None
    created_at: datetime | None = field(default_factory=_utcnow)
    expires_at: datetime | None = None


@model
class EvidenceLink:
    """Polymorphic link between an evidence file and any compliance entity.

    Stored in the account partition (account_id copied from the evidence) so
    "evidence linked to entity X" is one query rather than one per evidence file.
    """

    __partition__ = ("Account", "account_id")
    __sort__ = ("evidence_id", "entity_type", "entity_id")

    id: str | None = field(default_factory=_new_uuid)
    account_id: str | None = None
    evidence_id: str | None = None
    entity_type: str | None = None
    entity_id: str | None = None
    link_type: str | None = "primary"
    linked_by_user_id: str | None = None
    linked_at: datetime | None = field(default_factory=_utcnow)
    unlinked_at: datetime | None = None


@model
class AssessmentQuestionControl:
    """Mapping between assessment questions and controls with weight."""

    __partition__ = ("Ref", None)
    __sort__ = ("question_id", "control_id")

    id: str | None = field(default_factory=_new_uuid)
    question_id: str | None = None
    control_id: str | None = None
    weight: float | None = 1.0
    created_at: datetime | None = field(default_factory=_utcnow)


@model
class AuditLog:
    """Tamper-evident audit trail for all compliance-relevant actions."""

    __partition__ = ("AuditLog", "account_id")

    id: int | None = field(default_factory=_next_audit_id)
    account_id: str | None = None
    event_type: str | None = None
    event_category: str | None = None
    actor_user_id: str | None = None
    actor_email: str | None = None
    actor_ip: str | None = None
    entity_type: str | None = None
    entity_id: str | None = None
    entity_label: str | None = None
    correlation_id: str | None = None
    before_state: str | None = None
    after_state: str | None = None
    change_reason: str | None = None
    is_material: bool | None = False
    metadata_json: str | None = None
    occurred_at: datetime | None = field(default_factory=_utcnow)
    hash: str | None = None
    prev_hash: str | None = None


@model
class PendingPeopleTaskInstantiation:
    """Queue for Phase 4: people-control task instantiation from closed remediation tasks."""

    __partition__ = ("Account", "account_id")

    id: str | None = field(default_factory=_new_uuid)
    account_id: str | None = None
    control_id: str | None = None
    task_type: str | None = "acknowledge"
    source_plan_id: str | None = None
    source_task_id: str | None = None
    status: str | None = "pending"
    created_at: datetime | None = field(default_factory=_utcnow)
    instantiated_at: datetime | None = None


@model
class PeopleTask:
    """Recurring or one-off continuous compliance task (embedded mini-ISMS)."""

    __partition__ = ("Account", "account_id")
    __onupdate__ = ("updated_at",)

    id: str | None = field(default_factory=_new_uuid)
    account_id: str | None = None
    title: str | None = None
    description: str | None = ""
    task_type: str | None = None
    pdca_phase: str | None = None
    article_21_subsection: str | None = None
    frequency: str | None = None
    next_due_date: date | None = None
    assignee_user_id: str | None = None
    assignee_role: str | None = None
    related_control_id: str | None = None
    related_process_id: str | None = None
    related_plan_id: str | None = None
    requires_evidence: bool | None = False
    attestation_statement: str | None = None
    baseline_template_id: str | None = None
    isms_domain: str | None = None
    active: bool | None = True
    created_at: datetime | None = field(default_factory=_utcnow)
    updated_at: datetime | None = field(default_factory=_utcnow)

    @property
    def completions(self) -> list["PeopleTaskCompletion"]:
        return session_of(self).list(PeopleTaskCompletion, self.id)


@model
class Report:
    """Snapshot of a generated compliance report."""

    __partition__ = ("Account", "account_id")
    __lookups__ = {"lk_token": "document_id"}
    __unique__ = ("document_id",)

    id: str | None = field(default_factory=_new_uuid)
    account_id: str | None = None
    document_id: str | None = None
    period: str | None = None
    period_start: date | None = None
    period_end: date | None = None
    aggregate_score: float | None = None
    technical_score: float | None = None
    human_factor_score: float | None = None
    grade: str | None = None
    maturity_level: int | None = 1
    file_size_bytes: int | None = 0
    file_path: str | None = None
    content_hash: str | None = None
    generated_at: datetime | None = field(default_factory=_utcnow)
    generated_by_user_id: str | None = None


@model
class PeopleTaskCompletion:
    """One completion record per user per period for a people task."""

    __partition__ = ("PeopleTask", "people_task_id")
    __sort__ = ("user_id", "period_key")

    id: str | None = field(default_factory=_new_uuid)
    people_task_id: str | None = None
    user_id: str | None = None
    period_key: str | None = None
    attested_at: datetime | None = None
    attestation_response: str | None = None
    evidence_id: str | None = None
    created_at: datetime | None = field(default_factory=_utcnow)


ALL_MODELS = [Account, User, CloudCredential, AwsAccount, Scan, ScanResult, Assessment, AssessmentVersion, AssessmentResponse, Evidence, RemediationPlan, RemediationPlanMilestone, RemediationPlanLink, RemediationTask, Country, EntityTier, CountryControl, CountryDeadline, CountryAssessmentQuestion, BaseControl, AccountControl, ControlCampaign, CampaignTask, BusinessProcess, ProcessControl, OAuthState, EvidenceLink, AssessmentQuestionControl, AuditLog, PendingPeopleTaskInstantiation, PeopleTask, Report, PeopleTaskCompletion]
