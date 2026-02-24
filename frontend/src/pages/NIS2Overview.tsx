import { useNavigate } from 'react-router-dom'
import {
  Shield,
  AlertTriangle,
  CheckCircle,
  TrendingUp,
  ChevronRight,
  FileText,
  Users,
  Radar,
  Activity,
} from 'lucide-react'
import { useControls } from '../hooks/useControls'
import { Card, Button, StatCard, ProgressBar, SeverityBadge } from '../components/ui'
import { ControlStatus } from '../types/controls'

const statusColors: Record<ControlStatus, string> = {
  'Not Started': '#ef4444',
  'Planned': '#f97316',
  'Partial': '#f59e0b',
  'Implemented': '#10b981'
}

const statusBgColors: Record<ControlStatus, string> = {
  'Not Started': 'bg-red-500/10 border-red-500/20',
  'Planned': 'bg-orange-500/10 border-orange-500/20',
  'Partial': 'bg-yellow-500/10 border-yellow-500/20',
  'Implemented': 'bg-emerald-500/10 border-emerald-500/20'
}

export default function NIS2Overview() {
  const navigate = useNavigate()
  const { complianceScore, articleAreas, criticalGaps, employeeComplianceStats } = useControls()

  const score = complianceScore.overall
  const scoreColor = score >= 91 ? '#3b82f6' : score >= 71 ? '#10b981' : score >= 41 ? '#f59e0b' : '#ef4444'
  const scoreLabel = score >= 91 ? 'Excellent' : score >= 71 ? 'Good' : score >= 41 ? 'At Risk' : 'Critical'
  const scoreBg = score >= 91 ? 'from-blue-500/10' : score >= 71 ? 'from-emerald-500/10' : score >= 41 ? 'from-yellow-500/10' : 'from-red-500/10'

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-[26px] font-bold font-syne text-white">NIS2 Compliance Overview</h1>
          <p className="text-[14px] text-[#CBD8E8] mt-1">
            EU Directive 2022/2555 — Article 21 Security Measures
          </p>
        </div>
        <Button onClick={() => navigate('/reports')}>
          <FileText size={16} />
          Generate Audit Report
        </Button>
      </div>

      {/* Overall Readiness Score Banner */}
      <Card glow className={`relative overflow-hidden bg-gradient-to-br ${scoreBg} to-transparent`}>
        <div className="absolute top-0 right-0 w-64 h-64 bg-cyan-500/5 rounded-full blur-3xl -mr-32 -mt-32" />
        <div className="relative">
          <div className="flex items-center justify-between">
            <div className="flex-1">
              <div className="flex items-center gap-3 mb-2">
                <Shield size={24} className="text-cyan-400" />
                <h2 className="text-xl font-bold font-syne text-white">
                  Overall NIS2 Readiness Score
                </h2>
              </div>
              <p className="text-[14px] text-[#CBD8E8] mb-6">
                Weighted assessment across all Article 21 controls
              </p>

              {/* Score breakdown */}
              <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
                <div className={`p-4 rounded-lg bg-gradient-to-br ${scoreBg} to-transparent border border-cyan-500/20`}>
                  <div className="flex items-center gap-2 mb-2">
                    <Shield size={16} className="text-cyan-400" />
                    <span className="text-xs text-cyan-400 uppercase tracking-wider font-semibold">Overall</span>
                  </div>
                  <div className="text-4xl font-bold font-syne mb-1" style={{ color: scoreColor }}>
                    {score}%
                  </div>
                  <div className="text-xs font-semibold" style={{ color: scoreColor }}>
                    {scoreLabel}
                  </div>
                </div>

                <div className="p-4 rounded-lg bg-navy-900/60 border border-navy-700">
                  <div className="flex items-center gap-2 mb-2">
                    <Radar size={14} className="text-purple-400" />
                    <span className="text-xs text-[#94b4d1] uppercase tracking-wider font-semibold">Technical</span>
                  </div>
                  <div className="text-3xl font-bold font-syne text-white mb-1">{complianceScore.technical}%</div>
                  <ProgressBar value={complianceScore.technical} color="bg-purple-500" height="h-1.5" />
                </div>

                <div className="p-4 rounded-lg bg-navy-900/60 border border-navy-700">
                  <div className="flex items-center gap-2 mb-2">
                    <FileText size={14} className="text-blue-400" />
                    <span className="text-xs text-[#94b4d1] uppercase tracking-wider font-semibold">Organizational</span>
                  </div>
                  <div className="text-3xl font-bold font-syne text-white mb-1">{complianceScore.organizational}%</div>
                  <ProgressBar value={complianceScore.organizational} color="bg-blue-500" height="h-1.5" />
                </div>

                <div className="p-4 rounded-lg bg-navy-900/60 border border-navy-700">
                  <div className="flex items-center gap-2 mb-2">
                    <Users size={14} className="text-emerald-400" />
                    <span className="text-xs text-[#94b4d1] uppercase tracking-wider font-semibold">People</span>
                  </div>
                  <div className="text-3xl font-bold font-syne text-white mb-1">{complianceScore.people}%</div>
                  <ProgressBar value={complianceScore.people} color="bg-emerald-500" height="h-1.5" />
                </div>
              </div>

              {/* Status alert */}
              {score < 71 && (
                <div className={`mt-6 p-3 rounded-lg border flex items-start gap-2 ${
                  score >= 41 ? 'bg-yellow-500/8 border-yellow-500/15' : 'bg-red-500/8 border-red-500/15'
                }`}>
                  <AlertTriangle size={14} className={`${score >= 41 ? 'text-yellow-400' : 'text-red-400'} mt-0.5 flex-shrink-0`} />
                  <div className="flex-1">
                    <p className={`text-[13px] ${score >= 41 ? 'text-yellow-300' : 'text-red-300'}`}>
                      {score >= 41
                        ? 'Moderate compliance risk — prioritize high-severity gaps to reach 71%+ readiness'
                        : 'Critical compliance risk — immediate action required on Not Started and Partial controls'}
                    </p>
                  </div>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => navigate('/controls')}
                    className={score >= 41 ? 'text-yellow-400 hover:text-yellow-300' : 'text-red-400 hover:text-red-300'}
                  >
                    View Controls <ChevronRight size={12} />
                  </Button>
                </div>
              )}

              {score >= 91 && (
                <div className="mt-6 p-3 rounded-lg bg-blue-500/8 border border-blue-500/15 flex items-start gap-2">
                  <TrendingUp size={14} className="text-blue-400 mt-0.5 flex-shrink-0" />
                  <p className="text-[13px] text-blue-300">
                    Excellent compliance posture! Maintain this level through regular reviews and continuous monitoring.
                  </p>
                </div>
              )}
            </div>
          </div>
        </div>
      </Card>

      {/* Stats Bar */}
      <div className="grid grid-cols-2 lg:grid-cols-5 gap-4">
        <StatCard
          label="Controls"
          value={articleAreas.reduce((sum, area) => sum + area.controlCount, 0)}
          icon={<Shield size={18} className="text-navy-300" />}
          accent="text-white"
        />
        <StatCard
          label="Implemented"
          value={articleAreas.reduce((sum, area) => sum + area.implementedCount, 0)}
          icon={<CheckCircle size={18} className="text-emerald-400" />}
          accent="text-emerald-400"
        />
        <StatCard
          label="Critical Gaps"
          value={criticalGaps.length}
          icon={<AlertTriangle size={18} className="text-red-500" />}
          accent="text-red-500"
          trend="Requires attention"
        />
        <StatCard
          label="Employee Tasks"
          value={`${employeeComplianceStats.completionRate}%`}
          icon={<Users size={18} className="text-cyan-400" />}
          accent="text-cyan-400"
          trend={`${employeeComplianceStats.completedTasks}/${employeeComplianceStats.totalTasks} completed`}
        />
        <StatCard
          label="Article 21 Areas"
          value={articleAreas.length}
          icon={<Activity size={18} className="text-navy-300" />}
          accent="text-white"
        />
      </div>

      {/* NIS2 Article 21 Coverage Map */}
      <Card>
        <div className="flex items-center justify-between mb-5">
          <div>
            <h2 className="text-[18px] font-bold font-syne text-white">
              NIS2 Article 21 Coverage Map
            </h2>
            <p className="text-[13px] text-[#94b4d1] mt-1">Compliance status across all requirement areas</p>
          </div>
          <Button variant="ghost" size="sm" onClick={() => navigate('/controls')}>
            View All Controls <ChevronRight size={14} />
          </Button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
          {articleAreas.map(area => {
            const color = statusColors[area.status]
            const bgClass = statusBgColors[area.status]
            const progress = Math.round((area.implementedCount / area.controlCount) * 100)

            return (
              <div
                key={area.id}
                onClick={() => navigate('/controls')}
                className={`p-4 rounded-lg border cursor-pointer transition-all hover:border-cyan-500/40 ${bgClass}`}
              >
                <div className="flex items-start justify-between mb-3">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-xs font-mono text-[#94b4d1]">{area.article}</span>
                      <span
                        className="text-xs font-semibold px-2 py-0.5 rounded"
                        style={{
                          backgroundColor: `${color}20`,
                          color: color
                        }}
                      >
                        {area.status}
                      </span>
                    </div>
                    <h3 className="text-[15px] font-semibold text-white leading-snug">{area.name}</h3>
                  </div>
                </div>

                <div className="space-y-2">
                  <ProgressBar value={progress} />
                  <div className="flex items-center justify-between text-[13px]">
                    <span className="text-[#94b4d1]">
                      {area.implementedCount} of {area.controlCount} controls
                    </span>
                    <span className="font-semibold" style={{ color }}>
                      {progress}%
                    </span>
                  </div>
                </div>
              </div>
            )
          })}
        </div>
      </Card>

      {/* Critical Gaps */}
      <Card>
        <div className="flex items-center justify-between mb-5">
          <div>
            <h2 className="text-[18px] font-bold font-syne text-white">
              Top 5 Critical Gaps
            </h2>
            <p className="text-[13px] text-[#94b4d1] mt-1">Highest priority controls requiring attention</p>
          </div>
          <Button variant="ghost" size="sm" onClick={() => navigate('/controls')}>
            View All <ChevronRight size={14} />
          </Button>
        </div>

        {criticalGaps.length === 0 ? (
          <div className="text-center py-12">
            <CheckCircle size={48} className="text-emerald-400 mx-auto mb-4" />
            <h3 className="text-lg font-bold font-syne text-white mb-2">
              No Critical Gaps!
            </h3>
            <p className="text-[14px] text-[#CBD8E8] max-w-md mx-auto">
              All critical and high severity controls are at least partially implemented. Keep up the good work!
            </p>
          </div>
        ) : (
          <div className="space-y-2">
            {criticalGaps.map((control, i) => (
              <div
                key={control.id}
                onClick={() => navigate('/controls')}
                className="group flex items-center gap-4 p-3 rounded-lg bg-navy-900/40 hover:bg-navy-800/60 border border-navy-800 hover:border-navy-700 cursor-pointer transition-all"
                style={{ animationDelay: `${i * 50}ms` }}
              >
                <div className="flex-shrink-0">
                  <SeverityBadge severity={control.severity} />
                </div>

                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <h4 className="text-[15px] font-semibold text-white group-hover:text-cyan-400 transition-colors truncate">
                      {control.title}
                    </h4>
                  </div>
                  <div className="flex items-center gap-3 text-[13px]">
                    <span className="text-[#94b4d1] font-mono">{control.article}</span>
                    <span className="text-[#4a6580]">•</span>
                    <span className="text-[#94b4d1]">{control.category}</span>
                    <span className="text-[#4a6580]">•</span>
                    <span
                      className="font-semibold"
                      style={{ color: statusColors[control.status] }}
                    >
                      {control.status}
                    </span>
                  </div>
                </div>

                <div className="hidden sm:flex items-center gap-2 flex-shrink-0">
                  <span className="text-[13px] text-[#94b4d1]">{control.owner}</span>
                  <ChevronRight size={14} className="text-[#4a6580] group-hover:text-cyan-400 transition-colors" />
                </div>
              </div>
            ))}
          </div>
        )}
      </Card>

      {/* Quick Actions */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card className="hover:border-cyan-500/40 transition-all cursor-pointer" onClick={() => navigate('/controls')}>
          <div className="flex items-start gap-4">
            <div className="p-3 rounded-lg bg-cyan-500/10 border border-cyan-500/20">
              <Shield size={24} className="text-cyan-400" />
            </div>
            <div className="flex-1">
              <h3 className="text-[15px] font-semibold text-white mb-1">Manage Controls</h3>
              <p className="text-[13px] text-[#94b4d1] leading-relaxed mb-3">
                View and update all NIS2 controls, upload evidence, and track progress
              </p>
              <Button variant="ghost" size="sm" className="text-cyan-400 hover:text-cyan-300 -ml-2">
                Open Controls Library <ChevronRight size={14} />
              </Button>
            </div>
          </div>
        </Card>

        <Card className="hover:border-emerald-500/40 transition-all cursor-pointer" onClick={() => navigate('/people-tasks')}>
          <div className="flex items-start gap-4">
            <div className="p-3 rounded-lg bg-emerald-500/10 border border-emerald-500/20">
              <Users size={24} className="text-emerald-400" />
            </div>
            <div className="flex-1">
              <h3 className="text-[15px] font-semibold text-white mb-1">People Tasks</h3>
              <p className="text-[13px] text-[#94b4d1] leading-relaxed mb-3">
                Track employee training and policy acknowledgments across all campaigns
              </p>
              <Button variant="ghost" size="sm" className="text-emerald-400 hover:text-emerald-300 -ml-2">
                View Campaigns <ChevronRight size={14} />
              </Button>
            </div>
          </div>
        </Card>

        <Card className="hover:border-purple-500/40 transition-all cursor-pointer" onClick={() => navigate('/scan')}>
          <div className="flex items-start gap-4">
            <div className="p-3 rounded-lg bg-purple-500/10 border border-purple-500/20">
              <Radar size={24} className="text-purple-400" />
            </div>
            <div className="flex-1">
              <h3 className="text-[15px] font-semibold text-white mb-1">Technical Scan</h3>
              <p className="text-[13px] text-[#94b4d1] leading-relaxed mb-3">
                Run AWS infrastructure scan to auto-populate technical control status
              </p>
              <Button variant="ghost" size="sm" className="text-purple-400 hover:text-purple-300 -ml-2">
                Run Scan <ChevronRight size={14} />
              </Button>
            </div>
          </div>
        </Card>
      </div>
    </div>
  )
}
