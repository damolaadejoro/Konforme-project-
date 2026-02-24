export type QuestionResponse = 'yes' | 'partial' | 'no' | 'na' | null
export type QuestionSeverity = 'critical' | 'high' | 'medium'

export interface HumanFactorQuestion {
  id: string
  category: string
  question: string
  description: string
  article: string
  articleTitle: string
  severity: QuestionSeverity
  guidance?: string
}

export interface QuestionAnswer {
  questionId: string
  response: QuestionResponse
  notes?: string
  timestamp: string
}

export interface HumanFactorAssessment {
  id: string
  completedAt: string | null
  answers: Record<string, QuestionAnswer>
  score: number
  totalQuestions: number
  answered: number
  gaps: HumanFactorGap[]
}

export interface HumanFactorGap {
  questionId: string
  question: string
  category: string
  article: string
  severity: QuestionSeverity
  response: QuestionResponse
  recommendation: string
}

export interface CategoryScore {
  category: string
  score: number
  answered: number
  total: number
  critical: number
  high: number
  medium: number
}

export interface CombinedCompliance {
  overallScore: number
  technicalScore: number
  humanFactorScore: number
  lastTechnicalScan: string
  lastHumanAssessment: string | null
  technicalWeight: number
  humanWeight: number
}
