import React from 'react'
import { AlertTriangle, CheckCircle, TrendingUp, Target } from 'lucide-react'
import type { ArticleScore, AssessmentGap } from '../../types/assessment'
import { MATURITY_LABELS, MATURITY_COLORS } from '../../types/assessment'
import { Card, ProgressBar } from '../ui'

interface AssessmentSummaryProps {
  overallScore: number
  articleScores: ArticleScore[]
  gaps: AssessmentGap[]
  answeredCount: number
  totalQuestions: number
}

export default function AssessmentSummary({
  overallScore,
  articleScores,
  gaps,
  answeredCount,
  totalQuestions,
}: AssessmentSummaryProps) {
  const scoreColor = overallScore >= 75 ? '#10b981' : overallScore >= 50 ? '#f59e0b' : '#ef4444'
  const scoreLabel = overallScore >= 75 ? 'Strong' : overallScore >= 50 ? 'Moderate' : 'Needs Improvement'
  const criticalGaps = gaps.filter(g => g.severity === 'critical')
  const highGaps = gaps.filter(g => g.severity === 'high')

  return (
    <div className="space-y-6">
      {/* Overall Score */}
      <Card glow>
        <div className="text-center py-4">
          <div className="text-5xl font-bold font-syne mb-2" style={{ color: scoreColor }}>
            {overallScore}%
          </div>
          <div className="text-lg font-semibold mb-1" style={{ color: scoreColor }}>
            {scoreLabel}
          </div>
          <p className="text-sm text-[#94b4d1]">
            {answeredCount} of {totalQuestions} questions assessed
          </p>
        </div>

        {/* Quick stats */}
        <div className="grid grid-cols-3 gap-4 mt-4 pt-4 border-t border-navy-700/50">
          <div className="text-center">
            <div className="text-2xl font-bold font-syne text-red-400">{criticalGaps.length}</div>
            <div className="text-xs text-[#94b4d1]">Critical Gaps</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold font-syne text-orange-400">{highGaps.length}</div>
            <div className="text-xs text-[#94b4d1]">High Gaps</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold font-syne text-emerald-400">
              {articleScores.filter(a => a.score >= 75).length}
            </div>
            <div className="text-xs text-[#94b4d1]">Strong Articles</div>
          </div>
        </div>
      </Card>

      {/* Per-article scores */}
      <Card>
        <h3 className="text-[16px] font-bold font-syne text-white mb-4">
          Article Maturity Scores
        </h3>
        <div className="space-y-3">
          {articleScores.map(art => {
            const artColor = art.score >= 75 ? '#10b981' : art.score >= 50 ? '#f59e0b' : art.score > 0 ? '#ef4444' : '#4a6580'
            return (
              <div key={art.article} className="p-3 rounded-lg bg-navy-900/40 border border-navy-800">
                <div className="flex items-center justify-between mb-2">
                  <div>
                    <span className="text-xs font-mono text-[#94b4d1]">{art.article}</span>
                    <h4 className="text-[13px] font-semibold text-white">{art.title}</h4>
                  </div>
                  <span className="text-lg font-bold font-syne" style={{ color: artColor }}>
                    {art.score}%
                  </span>
                </div>
                <ProgressBar
                  value={art.score}
                  color={art.score >= 75 ? 'bg-emerald-500' : art.score >= 50 ? 'bg-yellow-500' : 'bg-red-500'}
                  height="h-1.5"
                />
              </div>
            )
          })}
        </div>
      </Card>

      {/* Gap list */}
      {gaps.length > 0 && (
        <Card>
          <div className="flex items-center gap-2 mb-4">
            <AlertTriangle size={18} className="text-orange-400" />
            <h3 className="text-[16px] font-bold font-syne text-white">
              Gaps & Recommendations ({gaps.length})
            </h3>
          </div>
          <div className="space-y-3">
            {gaps.slice(0, 10).map((gap, i) => {
              const levelColor = gap.maturityLevel !== null ? MATURITY_COLORS[gap.maturityLevel] : '#4a6580'
              const levelLabel = gap.maturityLevel !== null ? MATURITY_LABELS[gap.maturityLevel] : 'N/A'
              const sevStyle = gap.severity === 'critical'
                ? 'bg-red-500/15 text-red-400 border-red-500/25'
                : gap.severity === 'high'
                ? 'bg-orange-500/15 text-orange-400 border-orange-500/25'
                : 'bg-yellow-500/15 text-yellow-400 border-yellow-500/25'

              return (
                <div key={gap.questionId} className="p-3 rounded-lg bg-navy-900/40 border border-navy-800">
                  <div className="flex items-start gap-3">
                    <span className="flex-shrink-0 w-6 h-6 rounded-full bg-navy-800 flex items-center justify-center text-xs font-semibold text-navy-300">
                      {i + 1}
                    </span>
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1 flex-wrap">
                        <span className={`inline-flex items-center px-2 py-0.5 rounded-md text-xs font-semibold border ${sevStyle}`}>
                          {gap.severity}
                        </span>
                        <span className="text-xs text-navy-400 font-mono">{gap.article}</span>
                        <span className="text-xs font-semibold px-2 py-0.5 rounded" style={{ backgroundColor: `${levelColor}20`, color: levelColor }}>
                          Level {gap.maturityLevel}: {levelLabel}
                        </span>
                      </div>
                      <p className="text-[13px] text-white font-medium mb-2">{gap.question}</p>
                      <div className="p-2.5 rounded bg-emerald-500/5 border border-emerald-500/15">
                        <div className="flex items-start gap-1.5">
                          <Target size={12} className="text-emerald-400 mt-0.5 flex-shrink-0" />
                          <p className="text-[12px] text-emerald-300 leading-relaxed">{gap.recommendation}</p>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              )
            })}
            {gaps.length > 10 && (
              <p className="text-center text-sm text-[#94b4d1]">
                + {gaps.length - 10} more gaps
              </p>
            )}
          </div>
        </Card>
      )}
    </div>
  )
}
