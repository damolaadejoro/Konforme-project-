import { useState, useEffect, useMemo } from 'react'
import {
  QuestionResponse,
  HumanFactorAssessment,
  QuestionAnswer,
  HumanFactorGap,
  CategoryScore,
} from '../types/humanFactor'
import { humanFactorQuestions, recommendations } from '../data/humanFactorQuestions'
import {
  submitAssessment,
  getAssessment,
  getStoredAuth,
  isConnected,
} from '../services/api'

const STORAGE_KEY = 'konforme_human_factor_assessment'

function calculateScore(answers: Record<string, QuestionAnswer>): number {
  const answeredQuestions = humanFactorQuestions.filter(
    q => answers[q.id] && answers[q.id].response !== null && answers[q.id].response !== 'na'
  )

  if (answeredQuestions.length === 0) return 0

  let totalWeight = 0
  let earnedWeight = 0

  answeredQuestions.forEach(q => {
    const weight = q.severity === 'critical' ? 3 : q.severity === 'high' ? 2 : 1
    totalWeight += weight

    const response = answers[q.id].response
    if (response === 'yes') {
      earnedWeight += weight
    } else if (response === 'partial') {
      earnedWeight += weight * 0.5
    }
  })

  return totalWeight === 0 ? 0 : Math.round((earnedWeight / totalWeight) * 100)
}

function identifyGaps(answers: Record<string, QuestionAnswer>): HumanFactorGap[] {
  const gaps: HumanFactorGap[] = []

  humanFactorQuestions.forEach(q => {
    const answer = answers[q.id]
    if (answer && (answer.response === 'no' || answer.response === 'partial')) {
      gaps.push({
        questionId: q.id,
        question: q.question,
        category: q.category,
        article: q.article,
        severity: q.severity,
        response: answer.response,
        recommendation: recommendations[q.id] || 'Address this gap to improve compliance.',
      })
    }
  })

  const severityOrder = { critical: 0, high: 1, medium: 2 }
  gaps.sort((a, b) => severityOrder[a.severity] - severityOrder[b.severity])

  return gaps
}

export function useHumanFactor() {
  const [answers, setAnswers] = useState<Record<string, QuestionAnswer>>({})
  const [isComplete, setIsComplete] = useState(false)
  const [backendScore, setBackendScore] = useState<number | null>(null)

  // Load from localStorage on mount
  useEffect(() => {
    const stored = localStorage.getItem(STORAGE_KEY)
    if (stored) {
      try {
        const data = JSON.parse(stored)
        setAnswers(data.answers || {})
        setIsComplete(data.completedAt !== null)
      } catch (e) {
        console.error('Failed to load human factor assessment', e)
      }
    }
  }, [])

  // Save to localStorage whenever answers change
  useEffect(() => {
    const assessment: HumanFactorAssessment = {
      id: 'hf-assessment-001',
      completedAt: isComplete ? new Date().toISOString() : null,
      answers,
      score: calculateScore(answers),
      totalQuestions: humanFactorQuestions.length,
      answered: Object.keys(answers).filter(
        k => answers[k].response !== null
      ).length,
      gaps: identifyGaps(answers),
    }
    localStorage.setItem(STORAGE_KEY, JSON.stringify(assessment))
  }, [answers, isComplete])

  const answerQuestion = (questionId: string, response: QuestionResponse, notes?: string) => {
    setAnswers(prev => ({
      ...prev,
      [questionId]: {
        questionId,
        response,
        notes,
        timestamp: new Date().toISOString(),
      },
    }))
  }

  const completeAssessment = async () => {
    setIsComplete(true)

    // Submit to backend if connected
    if (isConnected()) {
      const { accountId } = getStoredAuth()
      if (accountId) {
        try {
          const responses = humanFactorQuestions.map(q => {
            const answer = answers[q.id]
            return {
              question_id: q.id,
              response: answer?.response || 'no',
              notes: answer?.notes || '',
            }
          })
          const result = await submitAssessment(accountId, responses)
          setBackendScore(result.score)
        } catch (err) {
          console.error('Failed to submit assessment to backend:', err)
        }
      }
    }
  }

  const resetAssessment = () => {
    setAnswers({})
    setIsComplete(false)
    setBackendScore(null)
    localStorage.removeItem(STORAGE_KEY)
  }

  const assessment: HumanFactorAssessment = useMemo(() => {
    return {
      id: 'hf-assessment-001',
      completedAt: isComplete ? new Date().toISOString() : null,
      answers,
      score: backendScore ?? calculateScore(answers),
      totalQuestions: humanFactorQuestions.length,
      answered: Object.keys(answers).filter(
        k => answers[k].response !== null
      ).length,
      gaps: identifyGaps(answers),
    }
  }, [answers, isComplete, backendScore])

  const categoryScores: CategoryScore[] = useMemo(() => {
    const categories = Array.from(new Set(humanFactorQuestions.map(q => q.category)))
    return categories.map(cat => {
      const catQuestions = humanFactorQuestions.filter(q => q.category === cat)
      const answered = catQuestions.filter(q => answers[q.id] && answers[q.id].response !== null && answers[q.id].response !== 'na')

      let totalWeight = 0
      let earnedWeight = 0

      answered.forEach(q => {
        const weight = q.severity === 'critical' ? 3 : q.severity === 'high' ? 2 : 1
        totalWeight += weight
        const response = answers[q.id].response
        if (response === 'yes') earnedWeight += weight
        else if (response === 'partial') earnedWeight += weight * 0.5
      })

      const score = totalWeight === 0 ? 0 : Math.round((earnedWeight / totalWeight) * 100)

      return {
        category: cat,
        score,
        answered: answered.length,
        total: catQuestions.length,
        critical: catQuestions.filter(q => q.severity === 'critical').length,
        high: catQuestions.filter(q => q.severity === 'high').length,
        medium: catQuestions.filter(q => q.severity === 'medium').length,
      }
    })
  }, [answers])

  const progressPercent = Math.round(
    (assessment.answered / assessment.totalQuestions) * 100
  )

  return {
    assessment,
    answers,
    answerQuestion,
    completeAssessment,
    resetAssessment,
    isComplete,
    categoryScores,
    progressPercent,
  }
}
