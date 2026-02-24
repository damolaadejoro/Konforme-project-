import React from 'react'
import { useNavigate } from 'react-router-dom'
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
  PieChart,
  Pie,
} from 'recharts'
import {
  Users,
  AlertTriangle,
  CheckCircle,
  Edit,
  RotateCcw,
  ChevronRight,
  Lightbulb,
  Shield,
  TrendingUp,
  TrendingDown,
} from 'lucide-react'
import { useHumanFactor } from '../hooks/useHumanFactor'
import { Card, Button, SeverityBadge, ProgressBar, StatCard } from '../components/ui'

const CustomTooltip = ({ active, payload, label }: any) => {
  if (active && payload && payload.length) {
    return (
      <div className="bg-navy-800 border border-navy-700 rounded-lg px-3 py-2 text-xs shadow-xl">
        <p className="font-semibold text-white mb-1">{label}</p>
        <p className="text-cyan-400">Score: <span className="font-bold">{payload[0].value}%</span></p>
      </div>
    )
  }
  return null
}

export default function HumanFactorResults() {
  const navigate = useNavigate()
  const { assessment, categoryScores, resetAssessment, isComplete } = useHumanFactor()

  if (!isComplete && assessment.answered === 0) {
    return (
      <div className="max-w-3xl mx-auto">
        <Card className="text-center py-12">
          <AlertTriangle size={48} className="text-yellow-400 mx-auto mb-4" />
          <h2 className="text-xl font-bold font-syne text-white mb-2">
            No Assessment Completed Yet
          </h2>
          <p className="text-navy-300 mb-6">
            Complete the Human Factor questionnaire to view your results
          </p>
          <Button onClick={() => navigate('/human-factor')}>
            <Users size={16} />
            Start Assessment
          </Button>
        </Card>
      </div>
    )
  }

  const score = assessment.score
  const scoreColor = score >= 75 ? '#10b981' : score >= 50 ? '#f59e0b' : '#ef4444'
  const scoreLabel = score >= 75 ? 'Strong' : score >= 50 ? 'Moderate' : 'Needs Improvement'

  const criticalGaps = assessment.gaps.filter(g => g.severity === 'critical')
  const highGaps = assessment.gaps.filter(g => g.severity === 'high')
  const mediumGaps = assessment.gaps.filter(g => g.severity === 'medium')

  const donutData = [
    { name: 'Score', value: score },
    { name: 'Gap', value: 100 - score },
  ]

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold font-syne text-white">Human Factor Results</h1>
          <p className="text-sm text-navy-300 mt-1">
            Assessment of organizational security controls
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Button variant="secondary" onClick={() => navigate('/human-factor')}>
            <Edit size={15} />
            Edit Answers
          </Button>
          <Button
            variant="danger"
            onClick={() => {
              if (confirm('Reset assessment? This will delete all answers.')) {
                resetAssessment()
                navigate('/human-factor')
              }
            }}
          >
            <RotateCcw size={15} />
            Reset
          </Button>
        </div>
      </div>

      {/* Stats bar */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          label="Human Factor Score"
          value={`${score}%`}
          accent={`text-${score >= 75 ? 'emerald' : score >= 50 ? 'yellow' : 'red'}-400`}
          icon={<Shield size={18} style={{ color: scoreColor }} />}
          trend={scoreLabel}
        />
        <StatCard
          label="Critical Gaps"
          value={criticalGaps.length}
          accent="text-red-500"
          icon={<AlertTriangle size={18} className="text-red-500" />}
        />
        <StatCard
          label="High Gaps"
          value={highGaps.length}
          accent="text-orange-400"
          icon={<AlertTriangle size={18} className="text-orange-400" />}
        />
        <StatCard
          label="Questions Answered"
          value={`${assessment.answered}/${assessment.totalQuestions}`}
          icon={<CheckCircle size={18} className="text-cyan-400" />}
        />
      </div>

      {/* Score visual + category breakdown */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Score donut */}
        <Card glow className="flex flex-col items-center">
          <h2 className="text-base font-bold font-syne text-white mb-4 self-start">
            Overall Human Factor Score
          </h2>
          <div className="relative">
            <ResponsiveContainer width={220} height={220}>
              <PieChart>
                <Pie
                  data={donutData}
                  cx="50%"
                  cy="50%"
                  innerRadius={72}
                  outerRadius={96}
                  startAngle={90}
                  endAngle={-270}
                  paddingAngle={2}
                  dataKey="value"
                  stroke="none"
                >
                  <Cell fill={scoreColor} />
                  <Cell fill="#1a2d4a" />
                </Pie>
              </PieChart>
            </ResponsiveContainer>
            <div className="absolute inset-0 flex flex-col items-center justify-center">
              <span className="text-4xl font-bold font-syne" style={{ color: scoreColor }}>
                {score}%
              </span>
              <span className="text-xs font-semibold mt-1" style={{ color: scoreColor }}>
                {scoreLabel}
              </span>
            </div>
          </div>

          {/* Alert */}
          <div className={`mt-4 w-full p-3 rounded-lg border flex items-start gap-2 ${
            score >= 75 ? 'bg-emerald-500/8 border-emerald-500/15' :
            score >= 50 ? 'bg-yellow-500/8 border-yellow-500/15' :
            'bg-red-500/8 border-red-500/15'
          }`}>
            {score >= 75 ? (
              <TrendingUp size={14} className="text-emerald-400 mt-0.5 flex-shrink-0" />
            ) : (
              <TrendingDown size={14} className={`${score >= 50 ? 'text-yellow-400' : 'text-red-400'} mt-0.5 flex-shrink-0`} />
            )}
            <p className={`text-xs ${
              score >= 75 ? 'text-emerald-300' :
              score >= 50 ? 'text-yellow-300' :
              'text-red-300'
            }`}>
              {score >= 75
                ? 'Strong organizational controls — continue monitoring'
                : score >= 50
                ? 'Moderate controls — address high-priority gaps'
                : 'Significant gaps — immediate action required'}
            </p>
          </div>
        </Card>

        {/* Category bar chart */}
        <Card className="col-span-2">
          <h2 className="text-base font-bold font-syne text-white mb-5">
            Score by Category
          </h2>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart
              data={categoryScores}
              margin={{ top: 0, right: 10, left: -20, bottom: 0 }}
            >
              <CartesianGrid strokeDasharray="3 3" stroke="#1e3a5f" vertical={false} />
              <XAxis
                dataKey="category"
                tick={{ fill: '#7a9cc4', fontSize: 10 }}
                axisLine={false}
                tickLine={false}
                angle={-15}
                textAnchor="end"
                height={80}
              />
              <YAxis
                domain={[0, 100]}
                tick={{ fill: '#7a9cc4', fontSize: 11 }}
                axisLine={false}
                tickLine={false}
              />
              <Tooltip content={<CustomTooltip />} />
              <Bar dataKey="score" radius={[4, 4, 0, 0]} maxBarSize={60}>
                {categoryScores.map((entry, index) => (
                  <Cell
                    key={`cell-${index}`}
                    fill={
                      entry.score >= 75
                        ? '#10b981'
                        : entry.score >= 50
                        ? '#f59e0b'
                        : '#ef4444'
                    }
                    opacity={0.85}
                  />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>

          {/* Category details */}
          <div className="grid grid-cols-2 gap-3 mt-5">
            {categoryScores.map(c => (
              <div key={c.category} className="bg-navy-900/60 rounded-lg p-3">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-semibold text-white truncate">{c.category}</span>
                  <span className="text-xs font-bold" style={{
                    color: c.score >= 75 ? '#10b981' : c.score >= 50 ? '#f59e0b' : '#ef4444'
                  }}>
                    {c.score}%
                  </span>
                </div>
                <ProgressBar value={c.score} />
                <div className="flex justify-between mt-1.5">
                  <span className="text-xs text-navy-400">{c.answered}/{c.total} answered</span>
                  <span className="text-xs text-red-400">{c.critical}C {c.high}H {c.medium}M</span>
                </div>
              </div>
            ))}
          </div>
        </Card>
      </div>

      {/* Gaps & Recommendations */}
      {assessment.gaps.length > 0 && (
        <Card>
          <div className="flex items-center justify-between mb-5">
            <h2 className="text-base font-bold font-syne text-white">
              Gaps & Recommendations
            </h2>
            <span className="text-sm text-navy-400">{assessment.gaps.length} items</span>
          </div>

          <div className="space-y-3">
            {assessment.gaps.map((gap, i) => (
              <div
                key={gap.questionId}
                className="p-4 rounded-lg bg-navy-900/60 border border-navy-800 hover:border-navy-700 transition-all"
                style={{ animationDelay: `${i * 50}ms` }}
              >
                <div className="flex items-start gap-3 mb-3">
                  <span className="flex-shrink-0 w-6 h-6 rounded-full bg-navy-800 border border-navy-700 flex items-center justify-center text-xs font-bold text-navy-300">
                    {i + 1}
                  </span>
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-2">
                      <SeverityBadge severity={gap.severity} />
                      <span className="text-xs font-mono font-semibold text-cyan-400/80">{gap.article}</span>
                      <span className="text-xs text-navy-500">·</span>
                      <span className="text-xs text-navy-400">{gap.category}</span>
                    </div>
                    <h4 className="text-sm font-semibold text-white mb-1">{gap.question}</h4>
                    <div className="flex items-center gap-2 text-xs">
                      <span className="text-navy-500">Response:</span>
                      <span className={gap.response === 'partial' ? 'text-yellow-400' : 'text-red-400'}>
                        {gap.response === 'partial' ? 'Partial' : 'No'}
                      </span>
                    </div>
                  </div>
                </div>

                {/* Recommendation */}
                <div className="ml-9 p-3 rounded-lg bg-emerald-500/8 border border-emerald-500/15">
                  <div className="flex items-center gap-2 mb-2">
                    <Lightbulb size={13} className="text-emerald-400" />
                    <span className="text-xs font-bold text-emerald-400 uppercase tracking-wider">
                      Recommendation
                    </span>
                  </div>
                  <p className="text-sm text-emerald-200 leading-relaxed">{gap.recommendation}</p>
                </div>
              </div>
            ))}
          </div>
        </Card>
      )}

      {/* No gaps — success message */}
      {assessment.gaps.length === 0 && assessment.answered > 0 && (
        <Card className="text-center py-12">
          <CheckCircle size={48} className="text-emerald-400 mx-auto mb-4" />
          <h3 className="text-xl font-bold font-syne text-white mb-2">
            Excellent! No Gaps Found
          </h3>
          <p className="text-navy-300 max-w-md mx-auto">
            All organizational security controls are in place. Continue monitoring and reviewing quarterly to maintain compliance.
          </p>
        </Card>
      )}

      {/* Action buttons */}
      <div className="flex items-center justify-center gap-3 pt-4">
        <Button variant="secondary" onClick={() => navigate('/')}>
          <Shield size={15} />
          View Dashboard
        </Button>
        <Button onClick={() => navigate('/reports')}>
          View Full Report <ChevronRight size={15} />
        </Button>
      </div>
    </div>
  )
}
