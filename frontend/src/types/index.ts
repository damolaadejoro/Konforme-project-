export type Severity = 'critical' | 'high' | 'medium' | 'low' | 'pass'
export type FindingStatus = 'fail' | 'pass' | 'review'
export type ScanStatus = 'idle' | 'scanning' | 'complete' | 'error'

export interface Finding {
  id: string
  checkName: string
  description: string
  resource: string
  resourceType: string
  severity: Severity
  status: FindingStatus
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

export interface ScanResult {
  id: string
  accountName: string
  accountId: string
  region: string
  startedAt: string
  completedAt: string
  overallScore: number
  totalChecks: number
  passed: number
  failed: number
  criticalCount: number
  highCount: number
  mediumCount: number
  lowCount: number
  findings: Finding[]
  domainScores: DomainScore[]
}

export interface ScanCheckProgress {
  id: string
  checkName: string
  resource: string
  status: 'pending' | 'scanning' | 'pass' | 'fail'
  severity?: Severity
  duration?: number
}

export interface AWSCredentials {
  accessKey: string
  secretKey: string
  region: string
  accountName: string
}

export interface StatsCard {
  label: string
  value: string | number
  change?: number
  icon?: string
}
