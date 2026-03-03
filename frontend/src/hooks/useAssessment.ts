import { useState, useEffect, useMemo, useCallback } from 'react'
import type {
  MaturityLevel,
  QuestionResponse,
  ArticleScore,
  AssessmentGap,
  QuestionSeverity,
} from '../types/assessment'
import { SEVERITY_WEIGHTS, MATURITY_LABELS } from '../types/assessment'
import { ASSESSMENT_QUESTIONS, ARTICLES, QUESTIONS_BY_ARTICLE, QUESTION_MAP } from '../data/assessmentQuestions'
import {
  submitAssessmentV2,
  getAssessmentV2,
  autoSaveResponse,
  getStoredAuth,
  isConnected,
} from '../services/api'

const STORAGE_KEY = 'konforme_assessment_v2'

interface StoredAssessment {
  responses: Record<string, QuestionResponse>
  completedAt: string | null
}

function calculateArticleScores(responses: Record<string, QuestionResponse>): ArticleScore[] {
  return ARTICLES.map(art => {
    const questions = QUESTIONS_BY_ARTICLE[art.article] || []
    let earned = 0
    let max = 0
    let answered = 0

    questions.forEach(q => {
      const resp = responses[q.id]
      if (!resp) return // unanswered — skip entirely

      answered++ // count any response (including N/A) as answered

      if (resp.maturityLevel === null) return // N/A — don't include in score

      const weight = SEVERITY_WEIGHTS[q.severity]
      earned += (resp.maturityLevel / 4) * weight
      max += weight
    })

    return {
      article: art.article,
      title: art.title,
      score: max > 0 ? Math.round((earned / max) * 100 * 10) / 10 : 0,
      answered,
      total: questions.length,
    }
  })
}

function calculateOverallScore(responses: Record<string, QuestionResponse>): number {
  let totalEarned = 0
  let totalMax = 0

  ASSESSMENT_QUESTIONS.forEach(q => {
    const resp = responses[q.id]
    if (!resp || resp.maturityLevel === null) return

    const weight = SEVERITY_WEIGHTS[q.severity]
    totalEarned += (resp.maturityLevel / 4) * weight
    totalMax += weight
  })

  return totalMax > 0 ? Math.round((totalEarned / totalMax) * 100 * 10) / 10 : 0
}

function identifyGaps(responses: Record<string, QuestionResponse>): AssessmentGap[] {
  const gaps: AssessmentGap[] = []

  ASSESSMENT_QUESTIONS.forEach(q => {
    const resp = responses[q.id]
    if (!resp || resp.maturityLevel === null) return
    if (resp.maturityLevel <= 2) {
      gaps.push({
        questionId: q.id,
        question: q.question,
        article: q.article,
        severity: q.severity,
        maturityLevel: resp.maturityLevel,
        recommendation: q.guidance,
      })
    }
  })

  const severityOrder: Record<QuestionSeverity, number> = { critical: 0, high: 1, medium: 2 }
  gaps.sort((a, b) => {
    const sevDiff = severityOrder[a.severity] - severityOrder[b.severity]
    if (sevDiff !== 0) return sevDiff
    return (a.maturityLevel ?? 0) - (b.maturityLevel ?? 0)
  })

  return gaps
}

export function useAssessment() {
  const [responses, setResponses] = useState<Record<string, QuestionResponse>>({})
  const [isComplete, setIsComplete] = useState(false)
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [backendVersionId, setBackendVersionId] = useState<string | null>(null)

  // Load from localStorage on mount, then try backend
  useEffect(() => {
    const stored = localStorage.getItem(STORAGE_KEY)
    if (stored) {
      try {
        const data: StoredAssessment = JSON.parse(stored)
        setResponses(data.responses || {})
        setIsComplete(data.completedAt !== null)
      } catch (e) {
        console.error('Failed to load assessment', e)
      }
    }

    // Try to load from backend
    if (isConnected()) {
      const { accountId } = getStoredAuth()
      if (accountId) {
        getAssessmentV2(accountId)
          .then(data => {
            if (data.assessment) {
              const backendResponses: Record<string, QuestionResponse> = {}
              data.assessment.responses.forEach((r: any) => {
                backendResponses[r.question_id] = {
                  questionId: r.question_id,
                  maturityLevel: r.maturity_level,
                  notes: r.notes || '',
                  evidenceRefs: r.evidence_refs || [],
                }
              })
              setResponses(backendResponses)
              setIsComplete(data.assessment.status === 'submitted')
              setBackendVersionId(data.assessment.id)
            }
          })
          .catch(() => {})
          .finally(() => setLoading(false))
      } else {
        setLoading(false)
      }
    } else {
      setLoading(false)
    }
  }, [])

  // Persist to localStorage
  useEffect(() => {
    if (loading) return
    const data: StoredAssessment = {
      responses,
      completedAt: isComplete ? new Date().toISOString() : null,
    }
    localStorage.setItem(STORAGE_KEY, JSON.stringify(data))
  }, [responses, isComplete, loading])

  const answerQuestion = useCallback((questionId: string, maturityLevel: MaturityLevel, notes = '') => {
    setResponses(prev => ({
      ...prev,
      [questionId]: {
        questionId,
        maturityLevel,
        notes,
        evidenceRefs: prev[questionId]?.evidenceRefs || [],
        answeredAt: new Date().toISOString(),
      },
    }))

    // Auto-save to backend
    if (isConnected()) {
      const { accountId } = getStoredAuth()
      if (accountId) {
        autoSaveResponse(accountId, questionId, {
          question_id: questionId,
          maturity_level: maturityLevel,
          notes,
          evidence_refs: [],
        }).catch(() => {})
      }
    }
  }, [])

  const completeAssessment = useCallback(async () => {
    setSubmitting(true)
    try {
      if (isConnected()) {
        const { accountId } = getStoredAuth()
        if (accountId) {
          const apiResponses = ASSESSMENT_QUESTIONS.map(q => {
            const resp = responses[q.id]
            return {
              question_id: q.id,
              maturity_level: resp?.maturityLevel ?? null,
              notes: resp?.notes || '',
              evidence_refs: resp?.evidenceRefs || [],
            }
          })
          const result = await submitAssessmentV2(accountId, apiResponses)
          setBackendVersionId(result.id)
        }
      }
      setIsComplete(true)
    } catch (err) {
      console.error('Failed to submit assessment:', err)
      throw err
    } finally {
      setSubmitting(false)
    }
  }, [responses])

  const resetAssessment = useCallback(() => {
    setResponses({})
    setIsComplete(false)
    setBackendVersionId(null)
    localStorage.removeItem(STORAGE_KEY)
  }, [])

  const overallScore = useMemo(() => calculateOverallScore(responses), [responses])
  const articleScores = useMemo(() => calculateArticleScores(responses), [responses])
  const gaps = useMemo(() => identifyGaps(responses), [responses])

  const answeredCount = useMemo(
    () => Object.values(responses).filter(r => r.maturityLevel !== undefined).length,
    [responses]
  )

  const progressPercent = Math.round((answeredCount / ASSESSMENT_QUESTIONS.length) * 100)

  return {
    responses,
    answerQuestion,
    completeAssessment,
    resetAssessment,
    isComplete,
    loading,
    submitting,
    overallScore,
    articleScores,
    gaps,
    answeredCount,
    totalQuestions: ASSESSMENT_QUESTIONS.length,
    progressPercent,
    backendVersionId,
  }
}
