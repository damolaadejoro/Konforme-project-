import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { ClipboardCheck, ChevronRight, RotateCcw, Send, ChevronLeft } from 'lucide-react'
import { Card, Button, ProgressBar, InfoTooltip } from '../components/ui'
import { ARTICLES, QUESTIONS_BY_ARTICLE, ASSESSMENT_QUESTIONS } from '../data/assessmentQuestions'
import { useAssessment } from '../hooks/useAssessment'
import QuestionCard from '../components/assessment/QuestionCard'
import ArticleProgressCard from '../components/assessment/ArticleProgressCard'
import AssessmentSummary from '../components/assessment/AssessmentSummary'

export default function Assessment() {
  const navigate = useNavigate()
  const {
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
    totalQuestions,
    progressPercent,
  } = useAssessment()

  const [activeArticle, setActiveArticle] = useState(ARTICLES[0].article)
  const [showSummary, setShowSummary] = useState(false)

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[50vh]">
        <div className="animate-spin w-8 h-8 border-2 border-cyan-400 border-t-transparent rounded-full" />
      </div>
    )
  }

  if (isComplete || showSummary) {
    return (
      <div className="space-y-6">
        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-[26px] font-bold font-syne text-white">Assessment Complete</h1>
            <p className="text-[14px] text-[#CBD8E8] mt-1">
              NIS2 Maturity Assessment Results
            </p>
          </div>
          <div className="flex gap-2">
            <Button variant="secondary" onClick={() => { setShowSummary(false); if (isComplete) resetAssessment(); }}>
              <RotateCcw size={14} />
              {isComplete ? 'New Assessment' : 'Back to Questions'}
            </Button>
            <Button onClick={() => navigate('/assessment/history')}>
              View History <ChevronRight size={14} />
            </Button>
          </div>
        </div>

        <AssessmentSummary
          overallScore={overallScore}
          articleScores={articleScores}
          gaps={gaps}
          answeredCount={answeredCount}
          totalQuestions={totalQuestions}
        />
      </div>
    )
  }

  const activeQuestions = QUESTIONS_BY_ARTICLE[activeArticle] || []
  const activeIndex = ARTICLES.findIndex(a => a.article === activeArticle)

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-[26px] font-bold font-syne text-white flex items-center gap-2">
            NIS2 Assessment
            <InfoTooltip content="Evaluate your organization's NIS2 maturity by answering questions across all Article 21 areas" />
          </h1>
          <p className="text-[14px] text-[#CBD8E8] mt-1">
            Maturity assessment across all Article 21 requirement areas
          </p>
        </div>
        <div className="flex gap-2">
          {answeredCount > 0 && (
            <Button
              variant="secondary"
              onClick={() => setShowSummary(true)}
            >
              Preview Results
            </Button>
          )}
          <Button
            onClick={async () => {
              await completeAssessment()
              setShowSummary(true)
            }}
            loading={submitting}
            disabled={answeredCount < totalQuestions}
          >
            <Send size={14} />
            Submit Assessment
          </Button>
        </div>
      </div>

      {/* Progress banner */}
      <Card>
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-2">
            <ClipboardCheck size={18} className="text-cyan-400" />
            <span className="text-sm font-semibold text-white">
              Progress: {answeredCount} of {totalQuestions} questions
            </span>
          </div>
          <span className="text-sm font-bold text-cyan-400 flex items-center gap-1">
            {progressPercent}%
            <InfoTooltip content="Percentage of assessment questions answered" size={12} />
          </span>
        </div>
        <ProgressBar value={progressPercent} color="bg-cyan-500" height="h-2" />
        {answeredCount > 0 && (
          <p className="text-xs text-[#94b4d1] mt-2">
            Current score: <span className="font-semibold text-white">{overallScore}%</span>
            <InfoTooltip content="Real-time weighted score based on maturity levels selected so far" size={12} className="ml-1" />
          </p>
        )}
      </Card>

      {/* Main content: sidebar + questions */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Article navigation sidebar */}
        <div className="lg:col-span-1 space-y-2">
          <h3 className="text-xs font-semibold text-[#94b4d1] uppercase tracking-wider mb-3">
            NIS2 Articles
          </h3>
          {ARTICLES.map(art => {
            const artScore = articleScores.find(s => s.article === art.article)
            return (
              <ArticleProgressCard
                key={art.id}
                articleScore={artScore || { article: art.article, title: art.title, score: 0, answered: 0, total: 4 }}
                isActive={activeArticle === art.article}
                onClick={() => setActiveArticle(art.article)}
              />
            )
          })}
        </div>

        {/* Questions panel */}
        <div className="lg:col-span-3 space-y-4">
          {/* Article header */}
          <div className="flex items-center justify-between">
            <div>
              <span className="text-xs font-mono text-cyan-400">{activeArticle}</span>
              <h2 className="text-lg font-bold font-syne text-white">
                {ARTICLES.find(a => a.article === activeArticle)?.title}
              </h2>
            </div>
            <div className="flex gap-2">
              <Button
                variant="ghost"
                size="sm"
                disabled={activeIndex === 0}
                onClick={() => setActiveArticle(ARTICLES[activeIndex - 1].article)}
              >
                <ChevronLeft size={14} /> Previous
              </Button>
              <Button
                variant="ghost"
                size="sm"
                disabled={activeIndex === ARTICLES.length - 1}
                onClick={() => setActiveArticle(ARTICLES[activeIndex + 1].article)}
              >
                Next <ChevronRight size={14} />
              </Button>
            </div>
          </div>

          {/* Question cards */}
          {activeQuestions.map((q, i) => {
            const resp = responses[q.id]
            return (
              <QuestionCard
                key={q.id}
                question={q}
                maturityLevel={resp?.maturityLevel}
                notes={resp?.notes || ''}
                onAnswer={(level, notes) => answerQuestion(q.id, level, notes)}
                index={i}
              />
            )
          })}

          {/* Navigation footer */}
          <div className="flex justify-between pt-4">
            <Button
              variant="secondary"
              disabled={activeIndex === 0}
              onClick={() => setActiveArticle(ARTICLES[activeIndex - 1].article)}
            >
              <ChevronLeft size={14} /> Previous Article
            </Button>
            {activeIndex < ARTICLES.length - 1 ? (
              <Button
                onClick={() => setActiveArticle(ARTICLES[activeIndex + 1].article)}
              >
                Next Article <ChevronRight size={14} />
              </Button>
            ) : (
              <Button
                onClick={async () => {
                  if (answeredCount >= totalQuestions) {
                    await completeAssessment()
                  }
                  setShowSummary(true)
                }}
                loading={submitting}
              >
                <Send size={14} />
                {answeredCount >= totalQuestions ? 'Submit Assessment' : 'Preview Results'}
              </Button>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
