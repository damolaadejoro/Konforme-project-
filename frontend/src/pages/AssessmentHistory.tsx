import React from 'react'
import { useNavigate } from 'react-router-dom'
import { Clock, TrendingUp, ChevronRight, ArrowLeft } from 'lucide-react'
import { Card, Button } from '../components/ui'
import { useAssessmentHistory } from '../hooks/useAssessmentHistory'

export default function AssessmentHistory() {
  const navigate = useNavigate()
  const { versions, loading } = useAssessmentHistory()

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[50vh]">
        <div className="animate-spin w-8 h-8 border-2 border-cyan-400 border-t-transparent rounded-full" />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-[26px] font-bold font-syne text-white">Assessment History</h1>
          <p className="text-[14px] text-[#CBD8E8] mt-1">
            Track your NIS2 maturity progress over time
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="secondary" onClick={() => navigate('/assessment')}>
            <ArrowLeft size={14} />
            Back to Assessment
          </Button>
          <Button onClick={() => navigate('/assessment')}>
            New Assessment <ChevronRight size={14} />
          </Button>
        </div>
      </div>

      {versions.length === 0 ? (
        <Card>
          <div className="text-center py-16">
            <Clock size={48} className="text-navy-500 mx-auto mb-4" />
            <h3 className="text-lg font-bold font-syne text-white mb-2">No Assessments Yet</h3>
            <p className="text-[14px] text-[#CBD8E8] max-w-md mx-auto mb-6">
              Complete your first NIS2 maturity assessment to start tracking your progress. Each submitted assessment creates a new version.
            </p>
            <Button onClick={() => navigate('/assessment')}>
              Start Assessment <ChevronRight size={14} />
            </Button>
          </div>
        </Card>
      ) : (
        <>
          {/* Score trend summary */}
          {versions.length >= 2 && (
            <Card glow>
              <div className="flex items-center gap-3 mb-4">
                <TrendingUp size={20} className="text-cyan-400" />
                <h2 className="text-lg font-bold font-syne text-white">Score Trend</h2>
              </div>
              <div className="flex items-end gap-4 h-32">
                {[...versions].reverse().map((v, i) => {
                  const score = v.overallScore ?? 0
                  const barColor = score >= 75 ? 'bg-emerald-500' : score >= 50 ? 'bg-yellow-500' : 'bg-red-500'
                  return (
                    <div key={v.id} className="flex-1 flex flex-col items-center gap-1">
                      <span className="text-xs font-bold text-white">{score}%</span>
                      <div className="w-full bg-navy-800 rounded-t-lg relative" style={{ height: '100px' }}>
                        <div
                          className={`absolute bottom-0 w-full rounded-t-lg transition-all ${barColor}`}
                          style={{ height: `${score}%` }}
                        />
                      </div>
                      <span className="text-[10px] text-[#94b4d1]">v{v.version}</span>
                    </div>
                  )
                })}
              </div>
            </Card>
          )}

          {/* Version list */}
          <Card>
            <h2 className="text-[18px] font-bold font-syne text-white mb-4">
              All Versions ({versions.length})
            </h2>
            <div className="space-y-3">
              {versions.map((v, i) => {
                const score = v.overallScore ?? 0
                const scoreColor = score >= 75 ? '#10b981' : score >= 50 ? '#f59e0b' : '#ef4444'
                const prevScore = i < versions.length - 1 ? (versions[i + 1].overallScore ?? 0) : null
                const delta = prevScore !== null ? score - prevScore : null

                return (
                  <div
                    key={v.id}
                    className="flex items-center gap-4 p-4 rounded-lg bg-navy-900/40 border border-navy-800 hover:border-navy-600 transition-all"
                  >
                    <div className="flex-shrink-0 w-10 h-10 rounded-full bg-navy-800 flex items-center justify-center">
                      <span className="text-sm font-bold text-cyan-400">v{v.version}</span>
                    </div>

                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <h4 className="text-[15px] font-semibold text-white">
                          Assessment v{v.version}
                        </h4>
                        <span className={`text-xs px-2 py-0.5 rounded font-semibold ${
                          v.status === 'submitted'
                            ? 'bg-emerald-500/15 text-emerald-400'
                            : 'bg-yellow-500/15 text-yellow-400'
                        }`}>
                          {v.status}
                        </span>
                      </div>
                      <p className="text-[13px] text-[#94b4d1]">
                        {new Date(v.submittedAt).toLocaleDateString('en-GB', {
                          day: 'numeric',
                          month: 'short',
                          year: 'numeric',
                          hour: '2-digit',
                          minute: '2-digit',
                        })}
                      </p>
                    </div>

                    <div className="text-right">
                      <div className="text-2xl font-bold font-syne" style={{ color: scoreColor }}>
                        {score}%
                      </div>
                      {delta !== null && (
                        <span className={`text-xs font-semibold ${delta >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                          {delta >= 0 ? '+' : ''}{delta.toFixed(1)}%
                        </span>
                      )}
                    </div>
                  </div>
                )
              })}
            </div>
          </Card>
        </>
      )}
    </div>
  )
}
