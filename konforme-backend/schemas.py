from datetime import datetime

from pydantic import BaseModel, EmailStr


# --- Auth ---

class RegisterRequest(BaseModel):
    model_config = {"extra": "forbid"}

    email: EmailStr
    password: str
    name: str


class LoginRequest(BaseModel):
    model_config = {"extra": "forbid"}

    email: EmailStr
    password: str


class ResetPasswordRequest(BaseModel):
    model_config = {"extra": "forbid"}

    email: EmailStr
    new_password: str


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    account_id: str
    account_name: str
    email: str


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


class AccountResponse(BaseModel):
    id: str
    name: str
    is_active: bool
    connected_at: datetime
    aws_accounts: list[AwsAccountResponse]


# --- Scan ---

class ScanStartRequest(BaseModel):
    model_config = {"extra": "forbid"}

    aws_account_id: str


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


class ScanResponse(BaseModel):
    id: str
    accountName: str
    accountId: str
    awsAccountId: str | None = None
    awsAlias: str | None = None
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
    lastTechnicalScan: str | None
    lastHumanAssessment: str | None
    technicalWeight: float
    humanWeight: float
    grade: str | None
    articleBreakdown: list[ArticleBreakdown]


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
