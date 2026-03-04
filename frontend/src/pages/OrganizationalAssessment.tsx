import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  FileText,
  CheckCircle,
  Circle,
  MinusCircle,
  XCircle,
  ChevronRight,
  ChevronDown,
  Info,
  Shield,
  BarChart3,
} from 'lucide-react'
import { useOrganizational } from '../hooks/useOrganizational'
import { organizationalQuestions, orgSections } from '../data/organizationalQuestions'
import { OrgQuestionResponse } from '../types/organizational'
import { Card, Button, ProgressBar, SeverityBadge } from '../components/ui'

function ResponseButton({
  response,
  selected,
  onClick,
}: {
  response: OrgQuestionResponse
  selected: boolean
  onClick: () => void
}) {
  const config = {
    yes: {
      icon: CheckCircle,
      label: 'Yes',
      color: selected ? 'bg-emerald-500/15 border-emerald-500/40 text-emerald-400' : 'border-navy-700 text-navy-300 hover:border-emerald-500/30 hover:text-emerald-400',
      iconColor: 'text-emerald-400',
    },
    partial: {
      icon: MinusCircle,
      label: 'Partial',
      color: selected ? 'bg-yellow-500/15 border-yellow-500/40 text-yellow-400' : 'border-navy-700 text-navy-300 hover:border-yellow-500/30 hover:text-yellow-400',
      iconColor: 'text-yellow-400',
    },
    no: {
      icon: XCircle,
      label: 'No',
      color: selected ? 'bg-red-500/15 border-red-500/40 text-red-400' : 'border-navy-700 text-navy-300 hover:border-red-500/30 hover:text-red-400',
      iconColor: 'text-red-400',
    },
    na: {
      icon: Circle,
      label: 'N/A',
      color: selected ? 'bg-navy-600/30 border-navy-600/60 text-navy-300' : 'border-navy-700 text-navy-400 hover:border-navy-600 hover:text-navy-300',
      iconColor: 'text-navy-400',
    },
  }

  const cfg = config[response as keyof typeof config]
  const Icon = cfg.icon

  return (
    <button
      onClick={onClick}
      className={`flex items-center gap-2 px-4 py-2 rounded-lg border text-sm font-medium transition-all ${cfg.color}`}
    >
      <Icon size={16} className={selected ? cfg.iconColor : ''} />
      {cfg.label}
    </button>
  )
}

function QuestionCard({
  question,
  answer,
  onAnswer,
}: {
  question: typeof organizationalQuestions[0]
  answer: OrgQuestionResponse
  onAnswer: (response: OrgQuestionResponse) => void
}) {
  const [showGuidance, setShowGuidance] = useState(false)

  return (
    <div className="glass-card rounded-xl p-5 space-y-4">
      {/* Question header */}
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1">
          <div className="flex items-center gap-3 mb-2">
            <SeverityBadge severity={question.severity} />
            <span className="text-xs font-mono font-semibold text-cyan-400/80">{question.article}</span>
          </div>
          <h3 className="text-base font-semibold text-white leading-snug">{question.question}</h3>
          <p className="text-sm text-navy-300 mt-2 leading-relaxed">{question.description}</p>
        </div>
        {answer && answer !== null && (
          <div className="flex-shrink-0">
            {answer === 'yes' && <CheckCircle size={20} className="text-emerald-400" />}
            {answer === 'partial' && <MinusCircle size={20} className="text-yellow-400" />}
            {answer === 'no' && <XCircle size={20} className="text-red-400" />}
            {answer === 'na' && <Circle size={20} className="text-navy-400" />}
          </div>
        )}
      </div>

      {/* Response buttons */}
      <div className="flex flex-wrap gap-2">
        <ResponseButton response="yes" selected={answer === 'yes'} onClick={() => onAnswer('yes')} />
        <ResponseButton response="partial" selected={answer === 'partial'} onClick={() => onAnswer('partial')} />
        <ResponseButton response="no" selected={answer === 'no'} onClick={() => onAnswer('no')} />
        <ResponseButton response="na" selected={answer === 'na'} onClick={() => onAnswer('na')} />
      </div>

      {/* Guidance toggle */}
      {question.guidance && (
        <button
          onClick={() => setShowGuidance(!showGuidance)}
          className="flex items-center gap-2 text-xs text-cyan-400 hover:text-cyan-300 transition-colors"
        >
          <Info size={13} />
          <span>{showGuidance ? 'Hide' : 'Show'} guidance</span>
          {showGuidance ? <ChevronDown size={13} /> : <ChevronRight size={13} />}
        </button>
      )}

      {/* Guidance content */}
      {showGuidance && question.guidance && (
        <div className="p-3 rounded-lg bg-cyan-500/8 border border-cyan-500/15 text-sm text-navy-200 leading-relaxed">
          {question.guidance}
        </div>
      )}
    </div>
  )
}

export default function OrganizationalAssessment() {
  const navigate = useNavigate()
  const { assessment, answers, answerQuestion, completeAssessment, progressPercent, isComplete } = useOrganizational()
  const [expandedSection, setExpandedSection] = useState<string | null>(orgSections[0])

  const handleAnswer = (questionId: string, response: OrgQuestionResponse) => {
    answerQuestion(questionId, response)
  }

  const handleComplete = () => {
    completeAssessment()
    navigate('/organizational/results')
  }

  const allAnswered = assessment.answered === assessment.totalQuestions

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold font-syne text-white">Organizational Assessment</h1>
          <p className="text-sm text-navy-300 mt-1">
            NIS2 organizational controls and policy assessment
          </p>
        </div>
        {isComplete && (
          <Button variant="secondary" onClick={() => navigate('/organizational/results')}>
            <BarChart3 size={16} />
            View Results
          </Button>
        )}
      </div>

      {/* Progress card */}
      <Card glow>
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <Shield size={16} className="text-cyan-400" />
            <h2 className="text-base font-bold font-syne text-white">Assessment Progress</h2>
          </div>
          <span className="text-sm font-semibold text-cyan-400">
            {assessment.answered} / {assessment.totalQuestions} questions
          </span>
        </div>
        <ProgressBar value={progressPercent} animated color="bg-cyan-500" height="h-2.5" />
        <div className="flex items-center justify-between mt-3 text-sm">
          <span className="text-navy-300">{progressPercent}% complete</span>
          {allAnswered && !isComplete && (
            <Button size="sm" onClick={handleComplete}>
              Complete Assessment <ChevronRight size={14} />
            </Button>
          )}
        </div>
      </Card>

      {/* Instructions */}
      <Card>
        <div className="flex items-start gap-3">
          <Info size={18} className="text-cyan-400 mt-0.5 flex-shrink-0" />
          <div className="text-sm text-navy-200 leading-relaxed space-y-2">
            <p className="font-semibold text-white">How to complete this assessment:</p>
            <ul className="space-y-1 text-navy-300">
              <li className="flex items-start gap-2">
                <ChevronRight size={14} className="text-cyan-400 mt-0.5 flex-shrink-0" />
                <span><strong className="text-emerald-400">Yes</strong> — Control is fully implemented and documented</span>
              </li>
              <li className="flex items-start gap-2">
                <ChevronRight size={14} className="text-cyan-400 mt-0.5 flex-shrink-0" />
                <span><strong className="text-yellow-400">Partial</strong> — Control is partially in place but needs improvement</span>
              </li>
              <li className="flex items-start gap-2">
                <ChevronRight size={14} className="text-cyan-400 mt-0.5 flex-shrink-0" />
                <span><strong className="text-red-400">No</strong> — Control is not implemented or not documented</span>
              </li>
              <li className="flex items-start gap-2">
                <ChevronRight size={14} className="text-cyan-400 mt-0.5 flex-shrink-0" />
                <span><strong className="text-navy-400">N/A</strong> — Not applicable to your organization</span>
              </li>
            </ul>
            <p className="text-cyan-400 text-xs mt-3">
              Your answers are saved automatically to browser storage.
            </p>
          </div>
        </div>
      </Card>

      {/* Questions by section */}
      <div className="space-y-3">
        {orgSections.map(section => {
          const sectionQuestions = organizationalQuestions.filter(q => q.section === section)
          const sectionAnswered = sectionQuestions.filter(
            q => answers[q.id] && answers[q.id].response !== null
          ).length
          const isExpanded = expandedSection === section

          return (
            <div key={section} className="glass-card rounded-xl overflow-hidden">
              {/* Section header */}
              <button
                onClick={() => setExpandedSection(isExpanded ? null : section)}
                className="w-full flex items-center justify-between p-4 hover:bg-navy-800/40 transition-colors"
              >
                <div className="flex items-center gap-3">
                  <FileText size={18} className="text-cyan-400" />
                  <div className="text-left">
                    <h3 className="text-base font-bold font-syne text-white">{section}</h3>
                    <p className="text-xs text-navy-400 mt-0.5">
                      {sectionAnswered} of {sectionQuestions.length} answered
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <div className="flex items-center gap-2">
                    {sectionQuestions.map(q => {
                      const ans = answers[q.id]?.response
                      return (
                        <div
                          key={q.id}
                          className={`w-2 h-2 rounded-full ${
                            ans === 'yes' ? 'bg-emerald-400' :
                            ans === 'partial' ? 'bg-yellow-400' :
                            ans === 'no' ? 'bg-red-400' :
                            ans === 'na' ? 'bg-navy-600' :
                            'bg-navy-700'
                          }`}
                        />
                      )
                    })}
                  </div>
                  {isExpanded ? (
                    <ChevronDown size={18} className="text-cyan-400" />
                  ) : (
                    <ChevronRight size={18} className="text-navy-500" />
                  )}
                </div>
              </button>

              {/* Questions */}
              {isExpanded && (
                <div className="px-4 pb-4 space-y-3">
                  {sectionQuestions.map(q => (
                    <QuestionCard
                      key={q.id}
                      question={q}
                      answer={answers[q.id]?.response || null}
                      onAnswer={(response) => handleAnswer(q.id, response)}
                    />
                  ))}
                </div>
              )}
            </div>
          )
        })}
      </div>

      {/* Bottom CTA */}
      {allAnswered && !isComplete && (
        <Card className="text-center">
          <div className="flex flex-col items-center gap-4 py-4">
            <CheckCircle size={40} className="text-emerald-400" />
            <div>
              <h3 className="text-lg font-bold font-syne text-white">All Questions Answered</h3>
              <p className="text-sm text-navy-300 mt-1">
                Ready to complete your assessment and view results
              </p>
            </div>
            <Button size="lg" onClick={handleComplete}>
              Complete Assessment <ChevronRight size={16} />
            </Button>
          </div>
        </Card>
      )}
    </div>
  )
}
