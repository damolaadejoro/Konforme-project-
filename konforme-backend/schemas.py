from datetime import datetime

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


class CloudCredentialResponse(BaseModel):
    id: str
    provider: str
    alias: str
    is_active: bool
    added_at: datetime
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
    maturity_level: int | None = None  # 0-4, None = N/A
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


class RemediationTaskUpdate(BaseModel):
    model_config = {"extra": "forbid"}

    title: str | None = None
    description: str | None = None
    status: str | None = None
    priority: str | None = None
    assigned_to: str | None = None
    due_date: str | None = None


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
    status: str | None = None
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
    task_type: str
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
    role: str = "member"  # "admin" | "member"


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

    role: str  # "admin" | "member"
