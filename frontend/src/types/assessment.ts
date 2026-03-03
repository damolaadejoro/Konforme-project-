export type MaturityLevel = 0 | 1 | 2 | 3 | 4 | null // null = N/A

export type QuestionSeverity = 'critical' | 'high' | 'medium'

export interface AssessmentQuestion {
  id: string
  article: string
  articleTitle: string
  severity: QuestionSeverity
  question: string
  description: string
  guidance: string
}

export interface ArticleDefinition {
  id: string
  article: string
  title: string
}

export interface QuestionResponse {
  questionId: string
  maturityLevel: MaturityLevel
  notes: string
  evidenceRefs: string[]
  answeredAt?: string
}

export interface ArticleScore {
  article: string
  title: string
  score: number
  answered: number
  total: number
}

export interface AssessmentVersion {
  id: string
  version: number
  submittedAt: string
  overallScore: number | null
  status: 'draft' | 'submitted'
  articleScores: ArticleScore[]
  responses: QuestionResponse[]
}

export interface AssessmentVersionSummary {
  id: string
  version: number
  submittedAt: string
  overallScore: number | null
  status: string
}

export interface AssessmentGap {
  questionId: string
  question: string
  article: string
  severity: QuestionSeverity
  maturityLevel: MaturityLevel
  recommendation: string
}

export interface RemediationTask {
  id: string
  questionId: string
  title: string
  description: string
  status: 'open' | 'in_progress' | 'completed' | 'dismissed'
  priority: string
  assignedTo: string | null
  dueDate: string | null
  createdAt: string
  updatedAt: string
  completedAt: string | null
}

export interface VersionComparison {
  oldVersion: number
  newVersion: number
  oldScore: number | null
  newScore: number | null
  deltas: QuestionDelta[]
}

export interface QuestionDelta {
  questionId: string
  question: string
  article: string
  severity: string
  oldLevel: MaturityLevel
  newLevel: MaturityLevel
}

// Maturity level constants
export const MATURITY_LABELS: Record<number, string> = {
  0: 'Not Addressed',
  1: 'Aware',
  2: 'Ad-hoc',
  3: 'Documented',
  4: 'Practiced',
}

export const MATURITY_DESCRIPTIONS: Record<number, string> = {
  0: 'No measures or awareness in place',
  1: 'Awareness exists but no formal processes',
  2: 'Informal processes exist but not consistently applied',
  3: 'Formal, documented processes in place',
  4: 'Documented, practiced, tested, and continuously improved',
}

export const MATURITY_COLORS: Record<number, string> = {
  0: '#ef4444', // red
  1: '#f97316', // orange
  2: '#f59e0b', // amber
  3: '#3b82f6', // blue
  4: '#10b981', // emerald
}

export const SEVERITY_WEIGHTS: Record<QuestionSeverity, number> = {
  critical: 3,
  high: 2,
  medium: 1,
}
