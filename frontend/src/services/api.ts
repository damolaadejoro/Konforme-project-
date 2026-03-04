const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'
const API_BASE = `${API_URL}/api/v1`

const AUTH_KEYS = {
  accountId: 'konforme_account_id',
  accountName: 'konforme_account_name',
  email: 'konforme_email',
  awsAccounts: 'konforme_aws_accounts',
  selectedAwsAccountId: 'konforme_selected_aws_account_id',
}

// --- AWS Account types ---

export interface AwsAccountInfo {
  id: string
  alias: string
  awsAccountId: string
  awsRegion: string
  isActive: boolean
  addedAt: string
}

// --- CSRF helper ---

function getCsrfToken(): string {
  const match = document.cookie.split('; ').find(row => row.startsWith('csrf_token='))
  return match ? match.split('=')[1] : ''
}

// --- Auth helpers ---

export function getStoredAuth() {
  let awsAccounts: AwsAccountInfo[] = []
  try {
    const raw = localStorage.getItem(AUTH_KEYS.awsAccounts)
    if (raw) awsAccounts = JSON.parse(raw)
  } catch { /* ignore */ }

  return {
    accountId: localStorage.getItem(AUTH_KEYS.accountId),
    accountName: localStorage.getItem(AUTH_KEYS.accountName),
    email: localStorage.getItem(AUTH_KEYS.email),
    awsAccounts,
    selectedAwsAccountId: localStorage.getItem(AUTH_KEYS.selectedAwsAccountId),
  }
}

export function isAuthenticated(): boolean {
  return !!localStorage.getItem(AUTH_KEYS.accountId)
}

// Backward-compatible alias
export const isConnected = isAuthenticated

export function clearAuth() {
  const keysToRemove: string[] = []
  for (let i = 0; i < localStorage.length; i++) {
    const key = localStorage.key(i)
    if (key && key.startsWith('konforme_')) {
      keysToRemove.push(key)
    }
  }
  keysToRemove.forEach(k => localStorage.removeItem(k))
}

// --- Refresh token logic ---

let refreshPromise: Promise<boolean> | null = null

async function tryRefresh(): Promise<boolean> {
  if (refreshPromise) return refreshPromise
  refreshPromise = (async () => {
    try {
      const res = await fetch(`${API_BASE}/auth/refresh`, {
        method: 'POST',
        credentials: 'include',
      })
      if (!res.ok) return false
      const data = await res.json()
      // Update stored UI info
      localStorage.setItem(AUTH_KEYS.accountId, data.account_id)
      localStorage.setItem(AUTH_KEYS.accountName, data.account_name)
      localStorage.setItem(AUTH_KEYS.email, data.email)
      return true
    } catch {
      return false
    } finally {
      refreshPromise = null
    }
  })()
  return refreshPromise
}

// --- Fetch wrapper ---

async function apiFetch<T>(path: string, options: RequestInit = {}): Promise<T> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string> || {}),
  }

  // Add CSRF token for state-changing requests
  const method = (options.method || 'GET').toUpperCase()
  if (['POST', 'PATCH', 'DELETE', 'PUT'].includes(method)) {
    const csrf = getCsrfToken()
    if (csrf) {
      headers['X-CSRF-Token'] = csrf
    }
  }

  let res: Response
  try {
    res = await fetch(`${API_BASE}${path}`, {
      ...options,
      headers,
      credentials: 'include',
    })
  } catch {
    throw new Error('Unable to connect to the server. Please check your internet connection and try again.')
  }

  // On 401, try refreshing the token once
  const isAuthEndpoint = path.startsWith('/auth/')
  if (res.status === 401 && !isAuthEndpoint) {
    const refreshed = await tryRefresh()
    if (refreshed) {
      // Retry the original request with fresh cookies
      const retryHeaders = { ...headers }
      const newCsrf = getCsrfToken()
      if (newCsrf && ['POST', 'PATCH', 'DELETE', 'PUT'].includes(method)) {
        retryHeaders['X-CSRF-Token'] = newCsrf
      }
      try {
        res = await fetch(`${API_BASE}${path}`, {
          ...options,
          headers: retryHeaders,
          credentials: 'include',
        })
      } catch {
        throw new Error('Unable to connect to the server. Please check your internet connection and try again.')
      }
    }

    if (res.status === 401) {
      clearAuth()
      window.location.href = '/login'
      throw new Error('Session expired. Please log in again.')
    }
  }

  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: res.statusText }))
    const message = body.detail || `Something went wrong (${res.status})`
    throw new Error(message)
  }

  return res.json()
}

// --- Auth ---

interface AuthResponseRaw {
  access_token: string
  token_type: string
  account_id: string
  account_name: string
  email: string
}

function storeAuth(data: AuthResponseRaw) {
  // Clear all cached app data if switching to a different user
  const previousAccountId = localStorage.getItem(AUTH_KEYS.accountId)
  if (previousAccountId && previousAccountId !== data.account_id) {
    clearAuth()
  }

  localStorage.setItem(AUTH_KEYS.accountId, data.account_id)
  localStorage.setItem(AUTH_KEYS.accountName, data.account_name)
  localStorage.setItem(AUTH_KEYS.email, data.email)
}

export async function register(name: string, email: string, password: string): Promise<AuthResponseRaw> {
  const data = await apiFetch<AuthResponseRaw>('/auth/register', {
    method: 'POST',
    body: JSON.stringify({ name, email, password }),
  })
  storeAuth(data)
  return data
}

export async function login(email: string, password: string): Promise<AuthResponseRaw> {
  const data = await apiFetch<AuthResponseRaw>('/auth/login', {
    method: 'POST',
    body: JSON.stringify({ email, password }),
  })
  storeAuth(data)
  return data
}

export async function logout(): Promise<void> {
  try {
    await apiFetch('/auth/logout', { method: 'POST' })
  } catch { /* ignore */ }
  clearAuth()
}

export async function getMe(): Promise<{ account_id: string; account_name: string; email: string }> {
  return apiFetch('/auth/me')
}

export async function resetPassword(email: string, newPassword: string): Promise<void> {
  await apiFetch('/auth/reset-password', {
    method: 'POST',
    body: JSON.stringify({ email, new_password: newPassword }),
  })
}

// --- Account ---

interface AwsAccountResponseRaw {
  id: string
  alias: string
  aws_account_id: string
  aws_region: string
  is_active: boolean
  added_at: string
}

function mapAwsAccount(raw: AwsAccountResponseRaw): AwsAccountInfo {
  return {
    id: raw.id,
    alias: raw.alias,
    awsAccountId: raw.aws_account_id,
    awsRegion: raw.aws_region,
    isActive: raw.is_active,
    addedAt: raw.added_at,
  }
}

// --- AWS Account CRUD ---

export async function addAwsAccount(
  alias: string,
  accessKeyId: string,
  secretAccessKey: string,
  sessionToken: string | null,
  region: string
): Promise<AwsAccountInfo> {
  const raw = await apiFetch<AwsAccountResponseRaw>('/accounts/aws-accounts', {
    method: 'POST',
    body: JSON.stringify({
      alias,
      aws_access_key_id: accessKeyId,
      aws_secret_access_key: secretAccessKey,
      aws_session_token: sessionToken || null,
      region,
    }),
  })

  const mapped = mapAwsAccount(raw)

  // Update stored list
  const stored = getStoredAuth()
  const updated = [...stored.awsAccounts, mapped]
  localStorage.setItem(AUTH_KEYS.awsAccounts, JSON.stringify(updated))

  return mapped
}

export async function removeAwsAccount(awsAccountId: string): Promise<void> {
  await apiFetch(`/accounts/aws-accounts/${awsAccountId}`, { method: 'DELETE' })

  // Update stored list
  const stored = getStoredAuth()
  const updated = stored.awsAccounts.filter(a => a.id !== awsAccountId)
  localStorage.setItem(AUTH_KEYS.awsAccounts, JSON.stringify(updated))

  // If removed account was selected, select another
  if (stored.selectedAwsAccountId === awsAccountId) {
    if (updated.length > 0) {
      localStorage.setItem(AUTH_KEYS.selectedAwsAccountId, updated[0].id)
    } else {
      localStorage.removeItem(AUTH_KEYS.selectedAwsAccountId)
    }
  }
}

export interface AccountInfoResponse {
  id: string
  name: string
  is_active: boolean
  connected_at: string
  aws_accounts: AwsAccountResponseRaw[]
}

export async function getAccountInfo(): Promise<AccountInfoResponse> {
  return apiFetch<AccountInfoResponse>('/accounts')
}

// --- Scan ---

export interface ScanStartResponse {
  scan_id: string
  status: string
}

export interface ScanFinding {
  id: string
  checkName: string
  description: string
  resource: string
  resourceType: string
  severity: string
  status: string
  article: string
  articleTitle: string
  region: string
  evidence: string
  remediation: string
  remediationSteps: string[]
  domain: string
  timestamp: string
}

export interface DomainScore {
  domain: string
  article: string
  score: number
  passed: number
  failed: number
  total: number
}

export interface ScanResponse {
  id: string
  accountName: string
  accountId: string
  awsAccountId: string | null
  awsAlias: string | null
  region: string
  startedAt: string
  completedAt: string | null
  status: string
  overallScore: number | null
  totalChecks: number
  passed: number
  failed: number
  criticalCount: number
  highCount: number
  mediumCount: number
  lowCount: number
  findings: ScanFinding[]
  domainScores: DomainScore[]
}

export async function startScan(accountId: string, awsAccountId: string): Promise<ScanStartResponse> {
  return apiFetch<ScanStartResponse>(`/scan/${accountId}`, {
    method: 'POST',
    body: JSON.stringify({ aws_account_id: awsAccountId }),
  })
}

export async function getScan(scanId: string): Promise<ScanResponse> {
  return apiFetch<ScanResponse>(`/scan/${scanId}`)
}

// --- Assessment ---

export interface AssessmentResponseData {
  id: string
  completedAt: string
  score: number
  totalQuestions: number
  answered: number
  gaps: Array<{
    questionId: string
    question: string
    category: string
    article: string
    severity: string
    response: string
    recommendation: string
  }>
}

export interface AssessmentDetailResponse {
  assessment: AssessmentResponseData | null
  questions: Array<{
    id: string
    category: string
    question: string
    description: string
    article: string
    articleTitle: string
    severity: string
    guidance: string
  }>
}

export async function submitAssessment(
  accountId: string,
  responses: Array<{ question_id: string; response: string; notes?: string }>
): Promise<AssessmentResponseData> {
  return apiFetch<AssessmentResponseData>(`/assessment/${accountId}`, {
    method: 'POST',
    body: JSON.stringify({ responses }),
  })
}

export async function getAssessment(accountId: string): Promise<AssessmentDetailResponse> {
  return apiFetch<AssessmentDetailResponse>(`/assessment/${accountId}`)
}

// --- Assessment V2 (Maturity) ---

export async function submitAssessmentV2(
  accountId: string,
  responses: Array<{ question_id: string; maturity_level: number | null; notes?: string; evidence_refs?: string[] }>
): Promise<any> {
  return apiFetch(`/assessment/${accountId}/v2`, {
    method: 'POST',
    body: JSON.stringify({ responses }),
  })
}

export async function getAssessmentV2(accountId: string): Promise<any> {
  return apiFetch(`/assessment/${accountId}`)
}

export async function getAssessmentHistory(accountId: string): Promise<any> {
  return apiFetch(`/assessment/${accountId}/history`)
}

export async function getAssessmentVersion(accountId: string, versionId: string): Promise<any> {
  return apiFetch(`/assessment/${accountId}/version/${versionId}`)
}

export async function autoSaveResponse(
  accountId: string,
  questionId: string,
  data: { question_id: string; maturity_level: number | null; notes?: string; evidence_refs?: string[] }
): Promise<any> {
  return apiFetch(`/assessment/${accountId}/response/${questionId}`, {
    method: 'PATCH',
    body: JSON.stringify(data),
  })
}

// --- Remediation ---

export async function getRemediationTasks(accountId: string): Promise<any[]> {
  return apiFetch(`/remediation/${accountId}`)
}

export async function createRemediationTask(
  accountId: string,
  task: { question_id: string; title: string; description?: string; priority?: string; assigned_to?: string | null; due_date?: string | null }
): Promise<any> {
  return apiFetch(`/remediation/${accountId}`, {
    method: 'POST',
    body: JSON.stringify(task),
  })
}

export async function updateRemediationTask(
  accountId: string,
  taskId: string,
  updates: { title?: string; description?: string; status?: string; priority?: string; assigned_to?: string | null; due_date?: string | null }
): Promise<any> {
  return apiFetch(`/remediation/${accountId}/${taskId}`, {
    method: 'PATCH',
    body: JSON.stringify(updates),
  })
}

// --- Score ---

export interface CombinedScoreResponse {
  overallScore: number | null
  technicalScore: number | null
  humanFactorScore: number | null
  lastTechnicalScan: string | null
  lastHumanAssessment: string | null
  technicalWeight: number
  humanWeight: number
  grade: string | null
  articleBreakdown: Array<{
    article: string
    articleTitle: string
    technicalScore: number | null
    humanScore: number | null
    combinedScore: number | null
  }>
}

export async function getCombinedScore(accountId: string, awsAccountId?: string): Promise<CombinedScoreResponse> {
  const params = awsAccountId ? `?aws_account_id=${awsAccountId}` : ''
  return apiFetch<CombinedScoreResponse>(`/score/${accountId}${params}`)
}

// --- Report ---

export interface ReportResponse {
  accountId: string
  accountName: string
  generatedAt: string
  overallScore: number | null
  grade: string | null
  criticalActions: Array<{
    checkId: string
    title: string
    severity: string
    article: string
    remediation: string
    resource: string
  }>
  warnings: Array<{
    checkId: string
    title: string
    severity: string
    article: string
    remediation: string
    resource: string
  }>
  humanGaps: Array<{
    questionId: string
    question: string
    category: string
    article: string
    severity: string
    response: string
    recommendation: string
  }>
  passingCount: number
  totalChecks: number
}

export async function getReport(accountId: string): Promise<ReportResponse> {
  return apiFetch<ReportResponse>(`/report/${accountId}`)
}
