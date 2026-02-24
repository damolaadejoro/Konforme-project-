export type OrgQuestionResponse = 'yes' | 'partial' | 'no' | 'na' | null
export type OrgQuestionSeverity = 'critical' | 'high' | 'medium'

export interface OrganizationalQuestion {
  id: string
  section: string
  question: string
  description: string
  article: string
  articleTitle: string
  severity: OrgQuestionSeverity
  guidance?: string
}

export interface OrganizationalAnswer {
  questionId: string
  response: OrgQuestionResponse
  notes?: string
  timestamp: string
}

export interface OrganizationalAssessment {
  id: string
  completedAt: string | null
  answers: Record<string, OrganizationalAnswer>
  score: number
  totalQuestions: number
  answered: number
  gaps: OrganizationalGap[]
}

export interface OrganizationalGap {
  questionId: string
  question: string
  section: string
  article: string
  severity: OrgQuestionSeverity
  response: OrgQuestionResponse
  recommendation: string
}

export interface SectionScore {
  section: string
  score: number
  answered: number
  total: number
  critical: number
  high: number
  medium: number
}
