import { useState, useEffect, useMemo } from 'react'
import {
  OrgQuestionResponse,
  OrganizationalAssessment,
  OrganizationalAnswer,
  OrganizationalGap,
  SectionScore,
} from '../types/organizational'
import { organizationalQuestions, orgRecommendations } from '../data/organizationalQuestions'

const STORAGE_KEY = 'konforme_organizational_assessment'

function calculateScore(answers: Record<string, OrganizationalAnswer>): number {
  const answeredQuestions = organizationalQuestions.filter(
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

function identifyGaps(answers: Record<string, OrganizationalAnswer>): OrganizationalGap[] {
  const gaps: OrganizationalGap[] = []

  organizationalQuestions.forEach(q => {
    const answer = answers[q.id]
    if (answer && (answer.response === 'no' || answer.response === 'partial')) {
      gaps.push({
        questionId: q.id,
        question: q.question,
        section: q.section,
        article: q.article,
        severity: q.severity,
        response: answer.response,
        recommendation: orgRecommendations[q.id] || 'Address this gap to improve compliance.',
      })
    }
  })

  const severityOrder = { critical: 0, high: 1, medium: 2 }
  gaps.sort((a, b) => severityOrder[a.severity] - severityOrder[b.severity])

  return gaps
}

export function useOrganizational() {
  const [answers, setAnswers] = useState<Record<string, OrganizationalAnswer>>({})
  const [isComplete, setIsComplete] = useState(false)

  useEffect(() => {
    const stored = localStorage.getItem(STORAGE_KEY)
    if (stored) {
      try {
        const data = JSON.parse(stored)
        setAnswers(data.answers || {})
        setIsComplete(data.completedAt !== null)
      } catch (e) {
        console.error('Failed to load organizational assessment', e)
      }
    }
  }, [])

  useEffect(() => {
    const assessment: OrganizationalAssessment = {
      id: 'org-assessment-001',
      completedAt: isComplete ? new Date().toISOString() : null,
      answers,
      score: calculateScore(answers),
      totalQuestions: organizationalQuestions.length,
      answered: Object.keys(answers).filter(
        k => answers[k].response !== null
      ).length,
      gaps: identifyGaps(answers),
    }
    localStorage.setItem(STORAGE_KEY, JSON.stringify(assessment))
  }, [answers, isComplete])

  const answerQuestion = (questionId: string, response: OrgQuestionResponse, notes?: string) => {
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

  const completeAssessment = () => {
    setIsComplete(true)
  }

  const resetAssessment = () => {
    setAnswers({})
    setIsComplete(false)
    localStorage.removeItem(STORAGE_KEY)
  }

  const assessment: OrganizationalAssessment = useMemo(() => {
    return {
      id: 'org-assessment-001',
      completedAt: isComplete ? new Date().toISOString() : null,
      answers,
      score: calculateScore(answers),
      totalQuestions: organizationalQuestions.length,
      answered: Object.keys(answers).filter(
        k => answers[k].response !== null
      ).length,
      gaps: identifyGaps(answers),
    }
  }, [answers, isComplete])

  const sectionScores: SectionScore[] = useMemo(() => {
    const sections = Array.from(new Set(organizationalQuestions.map(q => q.section)))
    return sections.map(section => {
      const sectionQuestions = organizationalQuestions.filter(q => q.section === section)
      const answered = sectionQuestions.filter(q => answers[q.id] && answers[q.id].response !== null && answers[q.id].response !== 'na')

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
        section,
        score,
        answered: answered.length,
        total: sectionQuestions.length,
        critical: sectionQuestions.filter(q => q.severity === 'critical').length,
        high: sectionQuestions.filter(q => q.severity === 'high').length,
        medium: sectionQuestions.filter(q => q.severity === 'medium').length,
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
    sectionScores,
    progressPercent,
  }
}
