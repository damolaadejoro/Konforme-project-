import React from 'react'
import { useNavigate } from 'react-router-dom'
import {
  PieChart,
  Pie,
  Cell,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts'
import {
  Shield,
  AlertTriangle,
  CheckCircle,
  XCircle,
  Radar,
  ChevronRight,
  TrendingDown,
  Lock,
  Eye,
  Database,
  Server,
  Users,
  FileText,
} from 'lucide-react'
import { mockScanResult } from '../data/mockData'
import { Card, StatCard, SeverityBadge, Button, ProgressBar } from '../components/ui'
import { useHumanFactor } from '../hooks/useHumanFactor'
import { useOrganizational } from '../hooks/useOrganizational'
import { format } from 'date-fns'

const score = mockScanResult.overallScore
const scoreColor =
  score >= 75 ? '#10b981' : score >= 50 ? '#f59e0b' : '#ef4444'
const scoreLabel =
  score >= 75 ? 'Compliant' : score >= 50 ? 'At Risk' : 'Non-Compliant'

const donutData = [
  { name: 'Score', value: score },
  { name: 'Gap', value: 100 - score },
]

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

const domainIcons: Record<string, React.ReactNode> = {
  'Access Control': <Lock size={14} className="text-cyan-400" />,
  'Monitoring': <Eye size={14} className="text-cyan-400" />,
  'Encryption': <Database size={14} className="text-cyan-400" />,
  'Business Continuity': <Server size={14} className="text-cyan-400" />,
}

export default function Dashboard() {
  const navigate = useNavigate()
  const { assessment: humanAssessment } = useHumanFactor()
  const { assessment: orgAssessment } = useOrganizational()
  const criticalFindings = mockScanResult.findings
    .filter(f => f.severity === 'critical' || f.severity === 'high')
    .slice(0, 5)

  // Calculate combined NIS2 compliance score
  const technicalScore = mockScanResult.overallScore
  const humanScore = humanAssessment.score
  const orgScore = orgAssessment.score
  const hasHumanAssessment = humanAssessment.answered > 0
  const hasOrgAssessment = orgAssessment.answered > 0

  // Weight: 40% technical, 30% human, 30% organizational (if assessments exist)
  let combinedScore = technicalScore
  if (hasHumanAssessment && hasOrgAssessment) {
    combinedScore = Math.round(technicalScore * 0.4 + humanScore * 0.3 + orgScore * 0.3)
  } else if (hasHumanAssessment) {
    combinedScore = Math.round(technicalScore * 0.6 + humanScore * 0.4)
  } else if (hasOrgAssessment) {
    combinedScore = Math.round(technicalScore * 0.6 + orgScore * 0.4)
  }

  const combinedColor = combinedScore >= 75 ? '#10b981' : combinedScore >= 50 ? '#f59e0b' : '#ef4444'
  const combinedLabel = combinedScore >= 75 ? 'Compliant' : combinedScore >= 50 ? 'At Risk' : 'Non-Compliant'

  const hasAllAssessments = hasHumanAssessment && hasOrgAssessment

  return (
    <div className="space-y-6">
      {/* Page header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold font-syne text-white">
            Compliance Overview
          </h1>
          <p className="text-sm text-navy-300 mt-1">
            NIS2 Article 21 assessment ·{' '}
            {format(new Date(mockScanResult.completedAt), 'MMMM d, yyyy')}
          </p>
        </div>
        <Button onClick={() => navigate('/scan')} size="md">
          <Radar size={16} />
          Run New Scan
        </Button>
      </div>

      {/* Combined NIS2 Score Banner */}
      <Card glow className="relative overflow-hidden">
        <div className="absolute top-0 right-0 w-64 h-64 bg-cyan-500/5 rounded-full blur-3xl -mr-32 -mt-32" />
        <div className="relative">
          <div className="flex items-center justify-between">
            <div className="flex-1">
              <div className="flex items-center gap-3 mb-2">
                <Shield size={20} className="text-cyan-400" />
                <h2 className="text-lg font-bold font-syne text-white">
                  Overall NIS2 Compliance Score
                </h2>
              </div>
              <p className="text-sm text-navy-300 mb-4">
                Combined assessment of technical infrastructure and organizational controls
              </p>

              {/* Score breakdown */}
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                <div className="p-3 rounded-lg bg-navy-900/60 border border-navy-700">
                  <div className="flex items-center gap-2 mb-1">
                    <Radar size={14} className="text-purple-400" />
                    <span className="text-xs text-navy-400 uppercase tracking-wider">Technical</span>
                  </div>
                  <div className="text-2xl font-bold font-syne text-red-400">{technicalScore}%</div>
                  <div className="text-xs text-navy-500 mt-1">AWS Infrastructure</div>
                </div>

                <div className="p-3 rounded-lg bg-navy-900/60 border border-navy-700">
                  <div className="flex items-center gap-2 mb-1">
                    <Users size={14} className="text-emerald-400" />
                    <span className="text-xs text-navy-400 uppercase tracking-wider">Human Factor</span>
                  </div>
                  <div className={`text-2xl font-bold font-syne ${hasHumanAssessment ? 'text-white' : 'text-navy-600'}`}>
                    {hasHumanAssessment ? `${humanScore}%` : '—'}
                  </div>
                  <div className="text-xs text-navy-500 mt-1">
                    {hasHumanAssessment ? 'People & Security' : (
                      <button
                        onClick={() => navigate('/human-factor')}
                        className="text-cyan-400 hover:text-cyan-300 transition-colors"
                      >
                        Start Assessment →
                      </button>
                    )}
                  </div>
                </div>

                <div className="p-3 rounded-lg bg-navy-900/60 border border-navy-700">
                  <div className="flex items-center gap-2 mb-1">
                    <FileText size={14} className="text-blue-400" />
                    <span className="text-xs text-navy-400 uppercase tracking-wider">Organizational</span>
                  </div>
                  <div className={`text-2xl font-bold font-syne ${hasOrgAssessment ? 'text-white' : 'text-navy-600'}`}>
                    {hasOrgAssessment ? `${orgScore}%` : '—'}
                  </div>
                  <div className="text-xs text-navy-500 mt-1">
                    {hasOrgAssessment ? 'Policies & Governance' : (
                      <button
                        onClick={() => navigate('/organizational')}
                        className="text-cyan-400 hover:text-cyan-300 transition-colors"
                      >
                        Start Assessment →
                      </button>
                    )}
                  </div>
                </div>

                <div className="p-3 rounded-lg bg-gradient-to-br from-cyan-500/10 to-cyan-500/5 border border-cyan-500/20">
                  <div className="flex items-center gap-2 mb-1">
                    <Shield size={14} className="text-cyan-400" />
                    <span className="text-xs text-cyan-400 uppercase tracking-wider font-semibold">Combined</span>
                  </div>
                  <div className="text-3xl font-bold font-syne" style={{ color: combinedColor }}>
                    {combinedScore}%
                  </div>
                  <div className="text-xs font-semibold mt-1" style={{ color: combinedColor }}>
                    {combinedLabel}
                  </div>
                </div>
              </div>

              {!hasAllAssessments && (
                <div className="mt-4 p-3 rounded-lg bg-yellow-500/8 border border-yellow-500/15 flex items-start gap-2">
                  <AlertTriangle size={14} className="text-yellow-400 mt-0.5 flex-shrink-0" />
                  <div className="flex-1">
                    <p className="text-xs text-yellow-300">
                      <strong>Incomplete Assessment:</strong> Complete {!hasHumanAssessment && !hasOrgAssessment ? 'both Human Factor and Organizational assessments' : !hasHumanAssessment ? 'the Human Factor assessment' : 'the Organizational assessment'} for full NIS2 compliance visibility
                    </p>
                  </div>
                  {!hasHumanAssessment && (
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => navigate('/human-factor')}
                      className="text-yellow-400 hover:text-yellow-300"
                    >
                      Human Factor <ChevronRight size={12} />
                    </Button>
                  )}
                  {!hasOrgAssessment && (
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => navigate('/organizational')}
                      className="text-yellow-400 hover:text-yellow-300"
                    >
                      Organizational <ChevronRight size={12} />
                    </Button>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>
      </Card>

      {/* Stats bar */}
      <div className="grid grid-cols-2 lg:grid-cols-5 gap-4">
        <StatCard
          label="NIS2 Score"
          value={`${score}%`}
          accent="text-red-400"
          icon={<Shield size={18} className="text-red-400" />}
          trend="Non-Compliant"
        />
        <StatCard
          label="Total Checks"
          value={mockScanResult.totalChecks}
          icon={<CheckCircle size={18} className="text-navy-300" />}
        />
        <StatCard
          label="Passed"
          value={mockScanResult.passed}
          accent="text-emerald-400"
          icon={<CheckCircle size={18} className="text-emerald-400" />}
        />
        <StatCard
          label="Failed"
          value={mockScanResult.failed}
          accent="text-red-400"
          icon={<XCircle size={18} className="text-red-400" />}
        />
        <StatCard
          label="Critical"
          value={mockScanResult.criticalCount}
          accent="text-red-500"
          icon={<AlertTriangle size={18} className="text-red-500" />}
          trend="Requires immediate action"
        />
      </div>

      {/* Main charts row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Score Donut */}
        <Card glow className="flex flex-col items-center">
          <h2 className="text-base font-bold font-syne text-white mb-4 self-start">
            Overall Compliance Score
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
            {/* Center text */}
            <div className="absolute inset-0 flex flex-col items-center justify-center">
              <span
                className="text-4xl font-bold font-syne"
                style={{ color: scoreColor }}
              >
                {score}%
              </span>
              <span className="text-xs font-semibold mt-1" style={{ color: scoreColor }}>
                {scoreLabel}
              </span>
            </div>
          </div>

          {/* Legend */}
          <div className="w-full mt-4 space-y-2">
            {[
              { label: 'Critical', count: mockScanResult.criticalCount, color: '#ef4444' },
              { label: 'High', count: mockScanResult.highCount, color: '#f97316' },
              { label: 'Medium', count: mockScanResult.mediumCount, color: '#f59e0b' },
              { label: 'Passed', count: mockScanResult.passed, color: '#10b981' },
            ].map(item => (
              <div key={item.label} className="flex items-center justify-between text-sm">
                <div className="flex items-center gap-2">
                  <div
                    className="w-2.5 h-2.5 rounded-full"
                    style={{ backgroundColor: item.color }}
                  />
                  <span className="text-navy-300">{item.label}</span>
                </div>
                <span className="font-semibold text-white">{item.count}</span>
              </div>
            ))}
          </div>

          {/* Alert */}
          <div className="mt-4 w-full p-3 rounded-lg bg-red-500/8 border border-red-500/15 flex items-start gap-2">
            <TrendingDown size={14} className="text-red-400 mt-0.5 flex-shrink-0" />
            <p className="text-xs text-red-300">
              Score below 50% — immediate remediation required for NIS2 compliance
            </p>
          </div>
        </Card>

        {/* Domain bar chart */}
        <Card className="col-span-2">
          <h2 className="text-base font-bold font-syne text-white mb-5">
            Score by NIS2 Domain
          </h2>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart
              data={mockScanResult.domainScores}
              margin={{ top: 0, right: 10, left: -20, bottom: 0 }}
            >
              <CartesianGrid strokeDasharray="3 3" stroke="#1e3a5f" vertical={false} />
              <XAxis
                dataKey="domain"
                tick={{ fill: '#7a9cc4', fontSize: 11 }}
                axisLine={false}
                tickLine={false}
              />
              <YAxis
                domain={[0, 100]}
                tick={{ fill: '#7a9cc4', fontSize: 11 }}
                axisLine={false}
                tickLine={false}
              />
              <Tooltip content={<CustomTooltip />} />
              <Bar dataKey="score" radius={[4, 4, 0, 0]} maxBarSize={60}>
                {mockScanResult.domainScores.map((entry, index) => (
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

          {/* Domain details */}
          <div className="grid grid-cols-2 gap-3 mt-5">
            {mockScanResult.domainScores.map(d => (
              <div key={d.domain} className="bg-navy-900/60 rounded-lg p-3">
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-1.5">
                    {domainIcons[d.domain]}
                    <span className="text-xs font-semibold text-white">{d.domain}</span>
                  </div>
                  <span className="text-xs text-navy-400">{d.article}</span>
                </div>
                <ProgressBar value={d.score} />
                <div className="flex justify-between mt-1.5">
                  <span className="text-xs text-emerald-400">{d.passed} pass</span>
                  <span className="text-xs text-red-400">{d.failed} fail</span>
                </div>
              </div>
            ))}
          </div>
        </Card>
      </div>

      {/* Recent critical findings */}
      <Card>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-base font-bold font-syne text-white">
            Critical & High Findings
          </h2>
          <Button variant="ghost" size="sm" onClick={() => navigate('/findings')}>
            View All <ChevronRight size={14} />
          </Button>
        </div>

        <div className="space-y-2">
          {criticalFindings.map((finding, i) => (
            <div
              key={finding.id}
              onClick={() => navigate('/findings')}
              className="group flex items-center gap-4 p-3 rounded-lg bg-navy-900/40 hover:bg-navy-800/60 border border-navy-800 hover:border-navy-700 cursor-pointer transition-all duration-200"
              style={{ animationDelay: `${i * 80}ms` }}
            >
              <SeverityBadge severity={finding.severity} />
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-white truncate group-hover:text-cyan-400 transition-colors">
                  {finding.checkName}
                </p>
                <p className="text-xs text-navy-400 truncate mt-0.5">{finding.resource}</p>
              </div>
              <div className="hidden sm:flex items-center gap-3">
                <span className="text-xs text-navy-400 font-mono">{finding.article}</span>
                <span className="text-xs text-navy-500">{finding.region}</span>
              </div>
              <ChevronRight size={14} className="text-navy-600 group-hover:text-cyan-400 transition-colors flex-shrink-0" />
            </div>
          ))}
        </div>
      </Card>

      {/* Scan info footer */}
      <div className="flex items-center justify-between py-3 px-4 rounded-lg bg-navy-900/40 border border-navy-800">
        <div className="flex items-center gap-4 text-xs text-navy-400">
          <span>Account: <span className="text-white">{mockScanResult.accountName} ({mockScanResult.accountId})</span></span>
          <span>Region: <span className="text-white">{mockScanResult.region}</span></span>
          <span>Duration: <span className="text-white">1m 40s</span></span>
        </div>
        <Button variant="secondary" size="sm" onClick={() => navigate('/scan')}>
          <Radar size={13} />
          Re-scan
        </Button>
      </div>
    </div>
  )
}
