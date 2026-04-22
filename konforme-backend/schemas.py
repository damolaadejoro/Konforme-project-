from datetime import datetime
from typing import Literal

from pydantic import BaseModel, EmailStr, Field, model_validator


# --- Auth ---

class RegisterRequest(BaseModel):
    model_config = {"extra": "forbid"}

    email: EmailStr
    password: str
    name: str
    country: str | None = None
    language: str | None = "en"


class LoginRequest(BaseModel):
    model_config = {"extra": "forbid"}

    email: EmailStr
    password: str


class ForgotPasswordRequest(BaseModel):
    model_config = {"extra": "forbid"}

    email: EmailStr


class ResetPasswordRequest(BaseModel):
    model_config = {"extra": "forbid"}

    token: str
    new_password: str


class UpdateEmailRequest(BaseModel):
    model_config = {"extra": "forbid"}

    email: EmailStr


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    account_id: str
    account_name: str
    email: str
    email_verified: bool = False
    country: str | None = None
    language: str | None = "en"
    user_id: str | None = None
    role: str | None = None


# --- AWS Account ---

class AwsAccountResponse(BaseModel):
    id: str
    alias: str
    aws_account_id: str
    aws_region: str
    is_active: bool
    added_at: datetime


class AwsAccountListResponse(BaseModel):
    aws_accounts: list[AwsAccountResponse]


class AddAwsAccountRequest(BaseModel):
    model_config = {"extra": "forbid"}

    alias: str
    aws_access_key_id: str
    aws_secret_access_key: str
    aws_session_token: str | None = None
    region: str = "eu-west-1"


# --- Account ---

class AccountUpdateRequest(BaseModel):
    model_config = {"extra": "forbid"}

    name: str | None = None
    email: EmailStr | None = None
    country: str | None = None
    language: str | None = None


class AccountResponse(BaseModel):
    id: str
    name: str
    is_active: bool
    country: str | None = None
    language: str | None = "en"
    connected_at: datetime
    aws_accounts: list[AwsAccountResponse]


# --- Cloud Credentials ---

class AddAzureCredentialRequest(BaseModel):
    model_config = {"extra": "forbid"}

    alias: str
    tenant_id: str
    client_id: str
    client_secret: str
    subscription_id: str


class AddAwsRoleRequest(BaseModel):
    model_config = {"extra": "forbid"}

    credential_id: str
    role_arn: str
    region: str = "eu-west-1"


class CloudCredentialResponse(BaseModel):
    id: str
    provider: str
    alias: str
    is_active: bool
    added_at: datetime
    connection_type: str | None = None  # "keys" | "role" | "client_secret" | "oauth"
    # AWS-specific (masked)
    aws_account_id: str | None = None
    aws_region: str | None = None
    # Azure-specific (masked)
    azure_subscription_id: str | None = None
    azure_tenant_id: str | None = None


class CloudCredentialListResponse(BaseModel):
    credentials: list[CloudCredentialResponse]


# --- Scan ---

class ScanStartRequest(BaseModel):
    model_config = {"extra": "forbid"}

    aws_account_id: str


class ScanStartWithProviderRequest(BaseModel):
    model_config = {"extra": "forbid"}

    credential_id: str
    provider: str = "aws"  # "aws" | "azure"


class ScanStartResponse(BaseModel):
    scan_id: str
    status: str


class FindingResponse(BaseModel):
    id: str
    checkName: str
    description: str
    resource: str
    resourceType: str
    severity: str
    status: str
    article: str
    articleTitle: str
    region: str
    evidence: str
    remediation: str
    remediationSteps: list[str]
    domain: str
    timestamp: str


class DomainScoreResponse(BaseModel):
    domain: str
    article: str
    score: float
    passed: int
    failed: int
    total: int


class ScanSummaryResponse(BaseModel):
    id: str
    status: str
    provider: str = "aws"
    startedAt: str
    completedAt: str | None
    overallScore: float | None
    totalChecks: int
    passed: int
    failed: int
    criticalCount: int
    highCount: int
    mediumCount: int
    lowCount: int


class ScanResponse(BaseModel):
    id: str
    accountName: str
    accountId: str
    provider: str = "aws"
    awsAccountId: str | None = None
    awsAlias: str | None = None
    cloudCredentialId: str | None = None
    region: str
    startedAt: str
    completedAt: str | None
    status: str
    overallScore: float | None
    totalChecks: int
    passed: int
    failed: int
    criticalCount: int
    highCount: int
    mediumCount: int
    lowCount: int
    findings: list[FindingResponse]
    domainScores: list[DomainScoreResponse]


# --- Assessment ---

class QuestionResponseItem(BaseModel):
    model_config = {"extra": "forbid"}

    question_id: str
    response: str  # yes | partial | no | na
    notes: str = ""


class AssessmentSubmitRequest(BaseModel):
    model_config = {"extra": "forbid"}

    responses: list[QuestionResponseItem]


class GapResponse(BaseModel):
    questionId: str
    question: str
    category: str
    article: str
    severity: str
    response: str
    recommendation: str


class AssessmentResponse(BaseModel):
    id: str
    completedAt: str
    score: float
    totalQuestions: int
    answered: int
    gaps: list[GapResponse]


class QuestionOut(BaseModel):
    id: str
    category: str
    question: str
    description: str
    article: str
    articleTitle: str
    severity: str
    guidance: str


class AssessmentDetailResponse(BaseModel):
    assessment: AssessmentResponse | None
    questions: list[QuestionOut]


# --- Assessment V2 (Maturity) ---

class MaturityResponseItem(BaseModel):
    model_config = {"extra": "forbid"}

    question_id: str
    maturity_level: int | None = Field(default=None, ge=0, le=4)  # 0-4, None = N/A
    notes: str = ""
    evidence_refs: list[str] = []


class AssessmentSubmitRequestV2(BaseModel):
    model_config = {"extra": "forbid"}

    responses: list[MaturityResponseItem]


class ArticleScoreOut(BaseModel):
    article: str
    title: str
    score: float
    answered: int
    total: int


class AssessmentVersionResponse(BaseModel):
    id: str
    version: int
    submittedAt: str
    overallScore: float | None
    status: str
    articleScores: list[ArticleScoreOut]
    responses: list[MaturityResponseItem]


class AssessmentVersionSummary(BaseModel):
    id: str
    version: int
    submittedAt: str
    overallScore: float | None
    status: str


class AssessmentHistoryResponse(BaseModel):
    versions: list[AssessmentVersionSummary]


class QuestionDelta(BaseModel):
    questionId: str
    question: str
    article: str
    severity: str
    oldLevel: int | None
    newLevel: int | None


class AssessmentCompareResponse(BaseModel):
    oldVersion: int
    newVersion: int
    oldScore: float | None
    newScore: float | None
    deltas: list[QuestionDelta]


class QuestionOutV2(BaseModel):
    id: str
    article: str
    articleTitle: str
    severity: str
    question: str
    description: str
    guidance: str


class AssessmentDetailResponseV2(BaseModel):
    assessment: AssessmentVersionResponse | None
    questions: list[QuestionOutV2]
    articles: list[ArticleScoreOut]


# --- Remediation ---

class RemediationTaskCreate(BaseModel):
    model_config = {"extra": "forbid"}

    question_id: str
    title: str
    description: str = ""
    priority: str = "medium"
    assigned_to: str | None = None
    due_date: str | None = None
    plan_id: str | None = None
    related_control_id: str | None = None
    severity: str = "medium"


class RemediationTaskResponse(BaseModel):
    id: str
    questionId: str
    title: str
    description: str
    status: str
    priority: str
    assignedTo: str | None
    dueDate: str | None
    createdAt: str
    updatedAt: str
    completedAt: str | None
    # Phase 3
    planId: str | None = None
    relatedControlId: str | None = None
    severity: str = "medium"
    autoGenerated: bool = False
    closureNote: str | None = None
    closureEvidenceId: str | None = None
    dismissedReason: str | None = None
    dismissedAt: str | None = None
    originalDueDate: str | None = None
    rescheduleCount: int = 0
    chronicSlip: bool = False


class RemediationTaskUpdate(BaseModel):
    model_config = {"extra": "forbid"}

    title: str | None = None
    description: str | None = None
    status: str | None = None
    priority: str | None = None
    assigned_to: str | None = None
    due_date: str | None = None


# --- Remediation Plans ---


class PlanLinkedEntity(BaseModel):
    model_config = {"extra": "forbid"}

    entity_type: str  # control|question|process
    entity_id: str


class CreateRemediationPlanRequest(BaseModel):
    model_config = {"extra": "forbid"}

    title: str
    description: str = ""
    treatment_type: Literal["mitigate", "transfer", "avoid", "accept"] = "mitigate"
    target_date: str | None = None
    linked_entities: list[PlanLinkedEntity] = []
    initial_task_ids: list[str] = []


class UpdateRemediationPlanRequest(BaseModel):
    model_config = {"extra": "forbid"}

    title: str | None = None
    description: str | None = None
    treatment_type: Literal["mitigate", "transfer", "avoid", "accept"] | None = None
    target_date: str | None = None
    change_reason: str | None = None  # required for material changes (treatment_type, target_date)


class MilestoneResponse(BaseModel):
    id: str
    title: str
    description: str
    targetDate: str | None
    completedAt: str | None
    displayOrder: int


class PlanLinkResponse(BaseModel):
    id: str
    entityType: str
    entityId: str


class RemediationPlanResponse(BaseModel):
    id: str
    title: str
    description: str
    treatmentType: str
    status: str
    targetDate: str | None
    createdByUserId: str | None
    approvedByUserId: str | None
    approvedAt: str | None
    rejectedByUserId: str | None
    rejectedAt: str | None
    rejectionReason: str | None
    createdAt: str
    updatedAt: str
    milestones: list[MilestoneResponse] = []
    links: list[PlanLinkResponse] = []
    taskCount: int = 0
    completedTaskCount: int = 0


class RemediationPlanSummary(BaseModel):
    id: str
    title: str
    treatmentType: str
    status: str
    targetDate: str | None
    createdAt: str
    taskCount: int = 0
    completedTaskCount: int = 0
    milestoneCount: int = 0
    completedMilestoneCount: int = 0


class PlanApprovalRequest(BaseModel):
    model_config = {"extra": "forbid"}

    action: Literal["approve", "reject"]
    rejection_reason: str | None = None


class MilestoneCreate(BaseModel):
    model_config = {"extra": "forbid"}

    title: str
    description: str = ""
    target_date: str | None = None
    display_order: int = 0


class MilestoneUpdate(BaseModel):
    model_config = {"extra": "forbid"}

    title: str | None = None
    description: str | None = None
    target_date: str | None = None
    display_order: int | None = None


class CloseTaskRequest(BaseModel):
    model_config = {"extra": "forbid"}

    closure_evidence_id: str | None = None
    closure_note: str | None = None
    confirm_assessment_update: bool = False


class DismissTaskRequest(BaseModel):
    model_config = {"extra": "forbid"}

    reason: str = Field(..., min_length=1)


class BulkDismissRequest(BaseModel):
    model_config = {"extra": "forbid"}

    task_ids: list[str] = Field(..., min_length=1)
    reason: str = Field(..., min_length=1)


class RescheduleTaskRequest(BaseModel):
    model_config = {"extra": "forbid"}

    new_due_date: str
    reason: str = Field(..., min_length=1)
    category: Literal["resource_constraint", "dependency", "scope_change", "other"] = "other"


# --- Evidence ---


class EvidenceResponse(BaseModel):
    id: str
    controlId: str
    filename: str
    fileSize: int
    contentType: str
    uploadedAt: str
    uploadedBy: str


# --- Score ---

class ArticleBreakdown(BaseModel):
    article: str
    articleTitle: str
    technicalScore: float | None
    humanScore: float | None
    combinedScore: float | None


class CombinedScoreResponse(BaseModel):
    overallScore: float | None
    technicalScore: float | None
    humanFactorScore: float | None
    controlsScore: float | None = None
    continuousComplianceRate: float | None = None
    lastTechnicalScan: str | None
    lastHumanAssessment: str | None
    technicalWeight: float
    humanWeight: float
    assessmentWeight: float = 0.35
    controlsWeight: float = 0.25
    grade: str | None
    articleBreakdown: list[ArticleBreakdown]


# --- Scoring Config ---

class ScoringConfig(BaseModel):
    model_config = {"extra": "forbid"}

    technical_weight: float = Field(default=0.40, ge=0.0, le=1.0)
    assessment_weight: float = Field(default=0.35, ge=0.0, le=1.0)
    controls_weight: float = Field(default=0.25, ge=0.0, le=1.0)
    preset: str | None = None

    @model_validator(mode="after")
    def weights_must_sum_to_one(self):
        total = self.technical_weight + self.assessment_weight + self.controls_weight
        if not (0.99 <= total <= 1.01):
            raise ValueError("Weights must sum to 1.0")
        return self


class ScoringConfigResponse(BaseModel):
    technicalWeight: float
    assessmentWeight: float
    controlsWeight: float
    preset: str | None = None


class ScoringConfigUpdateResponse(BaseModel):
    technicalWeight: float
    assessmentWeight: float
    controlsWeight: float
    preset: str | None = None
    previewOverallScore: float | None = None
    previewGrade: str | None = None


# --- Report ---

class ReportAction(BaseModel):
    checkId: str
    title: str
    severity: str
    article: str
    remediation: str
    resource: str


class ReportResponse(BaseModel):
    accountId: str
    accountName: str
    generatedAt: str
    overallScore: float | None
    grade: str | None
    criticalActions: list[ReportAction]
    warnings: list[ReportAction]
    humanGaps: list[GapResponse]
    passingCount: int
    totalChecks: int


# --- EU Countries ---

class EUAuthorityInfo(BaseModel):
    name: str
    acronym: str
    website: str
    email: str
    phone: str

class EUCountryInfo(BaseModel):
    code: str
    name: str
    localName: str
    authority: EUAuthorityInfo
    reportingUrl: str
    nis2TranspositionStatus: str  # "transposed" | "partial" | "pending"
    nis2NationalLaw: str
    primaryLanguage: str
    countryNotes: list[str] = []


# --- Country (DB-backed) ---

class CountryListItem(BaseModel):
    code: str
    name: str
    nameLocal: str | None = None
    transpositionStatus: str
    transpositionLawName: str | None = None
    dateEffective: str | None = None
    competentAuthorityName: str | None = None
    researchConfidence: str | None = None


class CountryResponse(BaseModel):
    code: str
    name: str
    nameLocal: str | None = None
    transpositionStatus: str
    transpositionLawName: str | None = None
    transpositionLawReference: str | None = None
    transpositionLawUrl: str | None = None
    datePublished: str | None = None
    dateEffective: str | None = None
    competentAuthorityName: str | None = None
    competentAuthorityUrl: str | None = None
    csirtName: str | None = None
    csirtUrl: str | None = None
    researchConfidence: str | None = None
    researchNotes: str | None = None


class EntityTierResponse(BaseModel):
    id: str
    tierKey: str
    localName: str | None = None
    description: str | None = None
    sectors: list = []
    sizeThresholds: dict = {}
    obligations: dict = {}
    penalties: dict = {}


class CountryControlResponse(BaseModel):
    id: str
    controlId: str
    euArticle: str | None = None
    nationalLegalReference: str | None = None
    nationalSpecification: str | None = None
    goesBeyondEu: bool = False
    appliesToTiers: list = []
    additionalRequirements: list = []
    isMandatory: bool = True


class CountryDeadlineResponse(BaseModel):
    id: str
    deadlineDate: str
    description: str | None = None
    appliesToTiers: list = []
    legalReference: str | None = None


class CountryAssessmentQuestionResponse(BaseModel):
    id: str
    baseQuestionId: str | None = None
    questionText: str
    helpText: str | None = None
    euArticle: str | None = None
    nationalLegalReference: str | None = None
    appliesToTiers: list = []
    domain: str | None = None
    weight: float = 1.0
    isAdditional: bool = False


class SetCountryRequest(BaseModel):
    model_config = {"extra": "forbid"}

    country_code: str
    entity_tier: str | None = None


# --- Base Controls ---


class BaseControlResponse(BaseModel):
    controlId: str
    title: str
    description: str
    article: str
    articleArea: str
    category: str
    severity: str
    isPeopleControl: bool


# --- Account Controls ---


class AccountControlItem(BaseModel):
    control_id: str
    status: str = "Not Started"
    owner: str = ""
    due_date: str | None = None
    notes: str = ""
    is_country_specific: bool = False


class AccountControlResponse(BaseModel):
    id: str
    controlId: str
    status: str
    owner: str
    dueDate: str | None
    notes: str
    isCountrySpecific: bool
    lastUpdated: str


class AccountControlBulkRequest(BaseModel):
    controls: list[AccountControlItem]


class AccountControlUpdate(BaseModel):
    status: Literal["Not Started", "Planned", "Partial", "Implemented"] | None = None
    owner: str | None = None
    due_date: str | None = None
    notes: str | None = None


# --- Campaigns ---


class CampaignEmployeeItem(BaseModel):
    employee_name: str
    employee_email: str
    department: str = ""


class CreateCampaignRequest(BaseModel):
    control_id: str
    control_name: str
    task_type: Literal["acknowledge", "quiz"]
    deadline: str
    employees: list[CampaignEmployeeItem]
    policy_content: str | None = None


class CampaignTaskResponse(BaseModel):
    id: str
    controlId: str
    campaignId: str
    employeeName: str
    employeeEmail: str
    department: str
    taskType: str
    status: str
    sentDate: str
    completedDate: str | None
    deadline: str
    score: int | None = None


class CampaignResponse(BaseModel):
    id: str
    controlId: str
    controlName: str
    taskType: str
    deadline: str
    createdAt: str
    policyContent: str | None = None
    tasks: list[CampaignTaskResponse]


class CampaignTaskUpdate(BaseModel):
    status: str | None = None
    score: int | None = None


# --- Team ---


class InviteRequest(BaseModel):
    model_config = {"extra": "forbid"}

    emails: list[EmailStr]
    role: Literal["admin", "member"] = "member"


class AcceptInviteRequest(BaseModel):
    model_config = {"extra": "forbid"}

    token: str
    name: str
    password: str


class TeamMemberResponse(BaseModel):
    id: str
    name: str
    email: str
    role: str
    emailVerified: bool
    isActive: bool
    inviteAccepted: bool
    createdAt: str


class UpdateMemberRoleRequest(BaseModel):
    model_config = {"extra": "forbid"}

    role: Literal["admin", "member"]


# --- Business Processes ---


class CreateBusinessProcessRequest(BaseModel):
    model_config = {"extra": "forbid"}

    name: str
    description: str = ""
    is_critical: bool = True
    owner: str = ""


class UpdateBusinessProcessRequest(BaseModel):
    model_config = {"extra": "forbid"}

    name: str | None = None
    description: str | None = None
    is_critical: bool | None = None
    owner: str | None = None


class ProcessControlItem(BaseModel):
    model_config = {"extra": "forbid"}

    control_id: str
    applicable: bool = True
    justification: str = ""


class ProcessControlResponse(BaseModel):
    id: str
    controlId: str
    applicable: bool
    justification: str
    createdAt: str


class BusinessProcessResponse(BaseModel):
    id: str
    name: str
    description: str
    isCritical: bool
    owner: str
    createdAt: str
    updatedAt: str
    controls: list[ProcessControlResponse] = []


class LinkControlsRequest(BaseModel):
    model_config = {"extra": "forbid"}

    controls: list[ProcessControlItem]


class SoAEntry(BaseModel):
    """Statement of Applicability entry — one per control across all processes."""
    controlId: str
    controlTitle: str
    applicable: bool
    justification: str
    linkedProcesses: list[str]  # process names


# --- Evidence v2 ---


class EvidenceUploadResponse(BaseModel):
    id: str
    filename: str
    fileSize: int
    contentType: str
    sha256: str | None = None
    description: str = ""
    tags: list[str] = []
    uploadedAt: str
    uploadedBy: str
    isDuplicate: bool = False


class EvidenceLinkRequest(BaseModel):
    model_config = {"extra": "forbid"}

    evidence_id: str
    entity_type: str
    entity_id: str
    link_type: str = "primary"


class EvidenceLinkResponse(BaseModel):
    id: str
    evidenceId: str
    entityType: str
    entityId: str
    linkType: str
    linkedAt: str


class EvidenceUpdateRequest(BaseModel):
    model_config = {"extra": "forbid"}

    description: str | None = None
    tags: list[str] | None = None


class EvidenceLinkedEntity(BaseModel):
    entityType: str
    entityId: str
    entityName: str


class EvidenceLibraryItem(BaseModel):
    id: str
    filename: str
    fileSize: int
    contentType: str
    sha256: str | None = None
    description: str = ""
    tags: list[str] = []
    uploadedAt: str
    uploadedBy: str
    linkCount: int = 0
    linkedEntities: list[EvidenceLinkedEntity] = []


class EvidenceLibraryResponse(BaseModel):
    items: list[EvidenceLibraryItem]
    total: int
    page: int
    perPage: int


# --- Audit Log ---


class AuditLogEntry(BaseModel):
    id: int
    eventType: str
    eventCategory: str
    actorEmail: str | None = None
    actorUserId: str | None = None
    entityType: str | None = None
    entityId: str | None = None
    entityLabel: str | None = None
    correlationId: str | None = None
    occurredAt: str
    changeReason: str | None = None
    isMaterial: bool = False
    beforeState: dict | None = None
    afterState: dict | None = None


class AuditLogResponse(BaseModel):
    items: list[AuditLogEntry]
    total: int
    page: int
    perPage: int


class ChainVerificationResponse(BaseModel):
    valid: bool
    total: int
    checked: int
    firstBrokenAt: int | None = None


# --- Question-Control Mapping ---


class QuestionControlMappingResponse(BaseModel):
    questionId: str
    controlId: str
    weight: float


# --- People Tasks (Continuous Compliance) ---


class CreatePeopleTaskRequest(BaseModel):
    model_config = {"extra": "forbid"}

    title: str
    description: str = ""
    task_type: Literal["attestation", "process_check", "evidence_submission", "policy_ack", "training"]
    pdca_phase: Literal["plan", "do", "check", "act"]
    article_21_subsection: str = Field(..., pattern=r"^[a-j]$")
    frequency: Literal["one_off", "monthly", "quarterly", "annual"]
    next_due_date: str | None = None
    assignee_user_id: str | None = None
    assignee_role: str | None = None
    related_control_id: str | None = None
    related_process_id: str | None = None
    related_plan_id: str | None = None
    requires_evidence: bool = False
    attestation_statement: str | None = None
    isms_domain: str | None = None


class UpdatePeopleTaskRequest(BaseModel):
    model_config = {"extra": "forbid"}

    title: str | None = None
    description: str | None = None
    task_type: str | None = None
    pdca_phase: str | None = None
    frequency: str | None = None
    next_due_date: str | None = None
    assignee_user_id: str | None = None
    assignee_role: str | None = None
    related_control_id: str | None = None
    related_process_id: str | None = None
    related_plan_id: str | None = None
    requires_evidence: bool | None = None
    attestation_statement: str | None = None
    isms_domain: str | None = None
    active: bool | None = None
    change_reason: str | None = None  # required for material fields


class PeopleTaskResponse(BaseModel):
    id: str
    title: str
    description: str
    taskType: str
    pdcaPhase: str
    article21Subsection: str
    frequency: str
    nextDueDate: str | None = None
    assigneeUserId: str | None = None
    assigneeRole: str | None = None
    relatedControlId: str | None = None
    relatedProcessId: str | None = None
    relatedPlanId: str | None = None
    requiresEvidence: bool
    attestationStatement: str | None = None
    baselineTemplateId: str | None = None
    ismsDomain: str | None = None
    active: bool
    createdAt: str
    updatedAt: str
    currentPeriodStatus: str | None = None
    completionCount: int = 0


class CompletePeopleTaskRequest(BaseModel):
    model_config = {"extra": "forbid"}

    attestation_response: str | None = None
    evidence_id: str | None = None


class PeopleTaskCompletionResponse(BaseModel):
    id: str
    peopleTaskId: str
    userId: str
    userName: str | None = None
    userEmail: str | None = None
    periodKey: str
    attestedAt: str | None = None
    attestationResponse: str | None = None
    evidenceId: str | None = None
    createdAt: str


class ReschedulePeopleTaskRequest(BaseModel):
    model_config = {"extra": "forbid"}

    new_due_date: str
    reason: str = Field(..., min_length=1)
    category: Literal["resource_constraint", "dependency", "scope_change", "other"] = "other"


class BaselineAssignment(BaseModel):
    template_id: str
    user_id: str | None = None
    role: str | None = None


class BaselineInstantiateRequest(BaseModel):
    model_config = {"extra": "forbid"}

    excluded_template_ids: list[str] = []
    assignments: list[BaselineAssignment] = []


class MyPeopleTaskItem(BaseModel):
    id: str
    title: str
    description: str
    taskType: str
    pdcaPhase: str
    article21Subsection: str
    frequency: str
    nextDueDate: str | None = None
    requiresEvidence: bool
    attestationStatement: str | None = None
    relatedControlId: str | None = None
    ismsDomain: str | None = None
    currentPeriodKey: str
    currentPeriodStatus: str  # completed | pending | overdue


class ISMSCoverageResponse(BaseModel):
    pdcaSummary: dict
    article21Coverage: list[dict]
    ismsDomainCoverage: list[dict] = []
    overallHealthScore: float
    overdueCount: int
    totalActive: int
    completedThisPeriod: int
